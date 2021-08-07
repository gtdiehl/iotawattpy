import json
import logging

import httpx

from .connection import Connection
from .sensor import Sensor

LOGGER = logging.getLogger(__name__)


class Iotawatt:

    """Creates an Iotawatt object that represents the physical hardware"""

    """with sensors connected to it"""

    def __init__(
        self,
        device_name,
        ip,
        websession: httpx.AsyncClient,
        username=None,
        password=None,
    ):
        self._device_name = device_name
        self._ip = ip
        self._connection = Connection(websession, self._ip)
        self._username = username
        self._password = password

        self._sensors = {}
        self._sensors["sensors"] = {}

        self._macAddress = ""

    """If Authentication is enabled, test the connection"""

    async def connect(self):
        url = "http://{}/status?wifi=yes".format(self._ip)
        results = await self._connection.get(url, self._username, self._password)
        if results.status_code == httpx.codes.OK:
            try:
                jsonResults = results.json()
            except json.JSONDecodeError:
                raise

            try:
                self._macAddress = jsonResults["wifi"]["mac"].replace(":", "")
                LOGGER.debug("MAC: %s", self._macAddress)
            except KeyError:
                raise
            return True
        elif results.status_code == 401:
            return False
        else:
            results.raise_for_status()

    """Returns an array of Sensor objects"""

    def getSensors(self):
        return self._sensors

    """Retrieves sensor data and updates the Sensor objects"""
    async def update(self, timespan=30):
        await self._refreshSensors(timespan)

    """Private helper functions"""

    """Retrieves list of Inputs and Outputs and associated Status from the IoTaWatt"""

    async def _getInputsandOutputs(self):
        url = "http://{}/status?inputs=yes&outputs=yes".format(self._ip)
        return await self._connection.get(url, self._username, self._password)

    def _createOrUpdateSensor(self, sensors, entity, channel_nbr, name, type, unit):
        if entity not in sensors:
            LOGGER.debug("%s: Creating Channel sensor %s", type, entity)
            sensors[entity] = Sensor(channel_nbr, name, type, unit, None, None, self._macAddress)
        else:
            sensor = sensors[entity]
            sensor.setName(name)
            sensor.setUnit(unit)
            sensor.setSensorID(self._macAddress)

    def _createOrUpdateSensorSet(self, sensors, entity, channel_nbr, name, type, unit):
        self._createOrUpdateSensor(sensors, entity, channel_nbr, name, type, unit)

        # Also add Energy sensors (the integral of Power) for all Power sensors
        if unit == "Watts":
            entity = entity + "_energy"
            name = name + ".wh"
            self._createOrUpdateSensor(sensors, entity, channel_nbr, name, type, "WattHours")


    async def _refreshSensors(self, timespan):
        sensors = self._sensors['sensors']

        response = await self._getInputsandOutputs()
        results = response.text
        results = json.loads(results)
        LOGGER.debug("IOResults: %s", results)
        inputs = results['inputs']
        outputs = results['outputs']

        query = await self._getQueryShowSeries()
        query = query.text
        query = json.loads(query)
        LOGGER.debug("Query: %s", query)

        for i in range(len(inputs)):
            channel_nbr = inputs[i]['channel']
            LOGGER.debug("In: Channel: %s - Name: %s", channel_nbr, query['series'][i]['name'])

            channel_input_name = "input_" + str(channel_nbr)
            channel_unit = query['series'][i]['unit']
            self._createOrUpdateSensorSet(sensors, channel_input_name, channel_nbr, query['series'][i]['name'], "Input", channel_unit)

        for i in range(len(outputs)):
            channel_name = str(outputs[i]['name'])
            LOGGER.debug("Out: Name: %s", channel_name)

            channel_output_name = "output_" + str(channel_name)
            channel_unit = outputs[i]['units']
            self._createOrUpdateSensorSet(sensors, channel_output_name, "N/A", channel_name, "Output", channel_unit)

        # Check and remove a sensor if it exists in memory but not from the query
        keys_to_be_removed = []
        LOGGER.debug("SensorKeys: %s", sensors.items())
        for entity, sensor in sensors.items():
            flag = False
            for i in range(len(query['series'])):
                if sensor.getUnit() == "WattHours":
                    queryName = query['series'][i]['name'] + ".wh"
                else:
                    queryName = query['series'][i]['name']
                LOGGER.debug("Compare: %s - %s", sensor.getName(), queryName)
                if sensor.getName() == queryName:
                    flag = True
                    break
                else:
                    continue
            if not flag:
                LOGGER.debug("Not Found: %s - %s", queryName, sensor.getName())
                LOGGER.debug("Adding to be removed: %s", entity)
                keys_to_be_removed.append(entity)

        if len(keys_to_be_removed) > 0:        
            for k in keys_to_be_removed:
                sensors.pop(k)
            LOGGER.debug("Check entity(s) removed: %s", sensors.items())
        

        # Update all entities, query depending on Unit
        current_query_entities = []
        integrated_query_entities = []
        for entity, sensor in sensors.items():
            if sensor.getUnit() == "WattHours":
                integrated_query_entities.append(entity)
            else:
                current_query_entities.append(entity)

        # Current (as in right now) measurements
        current_query_names = [ sensors[entity].getName() for entity in current_query_entities ]
        LOGGER.debug("Sen: %s", current_query_names)
        response = await self._getQuerySelectSeriesCurrent(current_query_names, timespan)
        values = json.loads(response.text)
        LOGGER.debug("Val: %s", values)

        # We can assume the same index for current_query_entities/current_query_names
        for idx in range(len(current_query_names)):
            sensor = sensors[current_query_entities[idx]]
            sensor.setValue(values[0][idx])

        # Integrated (as in integral) measurements
        integrated_query_names = [ sensors[entity].getName() for entity in integrated_query_entities ]
        LOGGER.debug("Sen: %s", integrated_query_names)
        response = await self._getQuerySelectSeriesIntegrate(integrated_query_names, "y")
        values = json.loads(response.text)
        LOGGER.debug("Val: %s", values)

        # We can assume the same index for integrated_query_entities/integrated_query_names
        for idx in range(len(integrated_query_names)):
            sensor = sensors[integrated_query_entities[idx]]
            sensor.setValue(values[0][idx+1])
            sensor.setBegin(values[0][0])


    async def _getQueryShowSeries(self):
        url = "http://{}/query?show=series".format(self._ip)
        LOGGER.debug("URL: %s", url)
        return await self._connection.get(url, self._username, self._password)

    async def _getQuerySelectSeriesCurrent(self, sensor_names, timespan):
        """Get current values using Query API.

        @param: sensor_names List of sensors
        @param: timespan Interval in seconds. Returns an average over the provided period
        """
        url = "http://{}/query".format(self._ip)
        strSeries = ",".join(sensor_names)
        url = url + f"?select=[{strSeries}]&begin=s-{timespan}s&end=s&group={timespan}s"
        LOGGER.debug("Querying with URL %s", url)
        return await self._connection.get(url, self._username, self._password)


    async def _getQuerySelectSeriesIntegrate(self, sensor_names, start):
        """Get integrated (summed) values using Query API.

        @param: sensor_names List of sensors
        @param: start Start time. ISO dates are supported. the following characters can be used as well:
        - y - Jan 1, of the current year
        - M - The first day of the current month
        - w - The first day of the current week (weeks start on Sunday)
        - d - The current day
        See also:https://docs.iotawatt.com/en/02_06_03/query.html#relative-time
        """
        url = "http://{}/query".format(self._ip)
        strSeries = ",".join(sensor_names)
        url = url + f"?select=[time.iso,{strSeries}]&begin={start}&end=s&group=all"
        LOGGER.debug("Querying with URL %s", url)
        return await self._connection.get(url, self._username, self._password)

