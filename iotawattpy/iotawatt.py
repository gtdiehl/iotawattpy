import json
import logging

import httpx

from .connection import Connection
from .sensor import Sensor

_LOGGER = logging.getLogger(__name__)

class Iotawatt:

    """Creates an Iotawatt object that represents the physical hardware"""
    """with sensors connected to it"""
    def __init__(self, device_name, ip, websession: httpx.AsyncClient, username=None, password=None):
        self._device_name = device_name
        self._ip = ip
        self._connection = Connection(websession, self._ip)
        self._username = username
        self._password = password

        self._sensors = {}
        self._sensors['sensors'] = {}

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
                self._macAddress = jsonResults['wifi']['mac'].replace(':', '')
                _LOGGER.debug("MAC: %s", self._macAddress)
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
            _LOGGER.debug("%s: Creating Channel sensor %s", type, entity)
            sensors[entity] = Sensor(channel_nbr, name, type, unit, None, self._macAddress)
        else:
            sensor = sensors[entity]
            sensor.setName(name)
            sensor.setUnit(unit)
            sensor.setSensorID(self._macAddress)


    async def _refreshSensors(self, timespan):
        sensors = self._sensors['sensors']

        response = await self._getInputsandOutputs()
        results = response.text
        results = json.loads(results)
        _LOGGER.debug("IOResults: %s", results)
        inputs = results['inputs']
        outputs = results['outputs']

        query = await self._getQueryShowSeries()
        query = query.text
        query = json.loads(query)
        _LOGGER.debug("Query: %s", query)

        for i in range(len(inputs)):
            channel_nbr = inputs[i]['channel']
            _LOGGER.debug("In: Channel: %s - Name: %s", channel_nbr, query['series'][i]['name'])

            channel_input_name = "input_" + str(channel_nbr)
            channel_unit = query['series'][i]['unit']
            self._createOrUpdateSensor(sensors, channel_input_name, channel_nbr, query['series'][i]['name'], "Input", channel_unit)


        for i in range(len(outputs)):
            channel_name = str(outputs[i]['name'])
            _LOGGER.debug("Out: Name: %s", channel_name)

            channel_output_name = "output_" + str(channel_name)
            channel_unit = query['series'][i]['unit']
            self._createOrUpdateSensor(sensors, channel_output_name, "N/A", channel_name, "Output", channel_unit)


        sensors_query_names = [ sensor.getName() for sensor in sensors.values() ]
        _LOGGER.debug("Sen: %s", sensors_query_names)
        response = await self._getQuerySelectSeriesCurrent(sensors_query_names, timespan)
        values = json.loads(response.text)
        _LOGGER.debug("Val: %s", values)

        # Update values, get item according to index from query
        for sensor in sensors.values():
            idx = sensors_query_names.index(sensor.getName())
            sensor.setValue(values[0][idx])


    async def _getQueryShowSeries(self):
        url = "http://{}/query?show=series".format(self._ip)
        _LOGGER.debug("URL: %s", url)
        return await self._connection.get(url, self._username, self._password)

    async def _getQuerySelectSeriesCurrent(self, sensor_names, timespan):
        """Get current values using Query API.

        @param: sensor_names List of sensors
        @param: timespan Interval in seconds. Returns an average over the provided period
        """
        url = "http://{}/query".format(self._ip)
        strSeries = ",".join(sensor_names)
        url = url + f"?select=[{strSeries}]&begin=s-{timespan}s&end=s&group={timespan}s"
        return await self._connection.get(url, self._username, self._password)
