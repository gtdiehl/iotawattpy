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
    async def update(self):
        await self._createSensors()

    """Private helper functions"""

    """Retrieves list of Inputs and Outputs and associated Status from the IoTaWatt"""
    async def _getInputsandOutputs(self):
        url = "http://{}/status?inputs=yes&outputs=yes".format(self._ip)
        return await self._connection.get(url, self._username, self._password)

    async def _createSensors(self):
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

        sensors_query_names = []
        for s in range(len(query['series'])):
            sensors_query_names.append(query['series'][s]['name'])
        _LOGGER.debug("Sen: %s", sensors_query_names)
        values = await self._getQuerySelectSeries(sensors_query_names)
        values = values.text
        values = json.loads(values)
        _LOGGER.debug("Val: %s", values)

        for i in range(len(inputs)):
            channel_name = inputs[i]['channel']
            _LOGGER.debug("In: Channel: %s - Name: %s - Value: %s %s", channel_name, query['series'][i]['name'], values[0][i+1], query['series'][i]['unit'])

            channel_input_name = "input_" + str(channel_name)
            if channel_input_name not in sensors:
                # Sensor doesn't exist yet, create it.
                _LOGGER.debug("In: Creating Channel sensor %s", channel_input_name)
                sensors[channel_input_name] = Sensor(channel_name, query['series'][i]['name'], "Input", query['series'][i]['unit'], values[0][i+1], self._macAddress)
            else:
                inputsensor = sensors[channel_input_name]
                inputsensor.setName(query['series'][i]['name'])
                inputsensor.setUnit(query['series'][i]['unit'])
                inputsensor.setValue(values[0][i+1])
                inputsensor.setSensorID(self._macAddress)

        for i in range(len(outputs)):
            channel_name = inputs[i]['channel']
            _LOGGER.debug("Out: Name: %s - Value: %s %s", outputs[i]['name'], outputs[i]['units'], outputs[i]['value'])

            channel_output_name = "output_" + str(channel_name)
            if channel_output_name not in sensors:
                _LOGGER.debug("Out: Creating Channel sensor %s", channel_output_name)
                sensors[channel_output_name] = Sensor("N/A", outputs[i]['name'], "Output", outputs[i]['units'], outputs[i]['value'], self._macAddress)
            else:
                outputsensor = sensors[channel_output_name]
                outputsensor.setUnit(outputs[i]['units'])
                outputsensor.setValue(outputs[i]['value'])
                outputsensor.setSensorID(self._macAddress)

    async def _getQueryShowSeries(self):
        url = "http://{}/query?show=series".format(self._ip)
        _LOGGER.debug("URL: %s", url)
        return await self._connection.get(url, self._username, self._password)

    async def _getQuerySelectSeries(self, sensor_names):
        url = "http://{}/query?select=[time.iso,".format(self._ip)
        delim = ","
        strSeries = delim.join(sensor_names)
        url = url + strSeries + "]&begin=s-5s&end=s&group=5s"
        return await self._connection.get(url, self._username, self._password)

