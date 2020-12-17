import json
import logging

import httpx

from .connection import Connection
from .sensor import Sensor


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
        try:
            jsonResults = results.json()
        except Exception:
            return False

        self._macAddress = jsonResults['wifi']['mac'].replace(':', '')
        logging.debug("MAC: %s", self._macAddress)
        return True

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
        response = await self._getInputsandOutputs()
        results = response.text
        results = json.loads(results)
        logging.debug("IOResults: %s", results)
        inputs = results['inputs']
        outputs = results['outputs']

        query = await self._getQueryShowSeries()
        query = query.text
        query = json.loads(query)
        logging.debug("Query: %s", query)

        sensors = []
        for s in range(len(query['series'])):
            sensors.append(query['series'][s]['name'])
        logging.debug("Sen: %s", sensors)
        values = await self._getQuerySelectSeries(sensors)
        values = values.text
        values = json.loads(values)
        logging.debug("Val: %s", values)

        for i in range(len(inputs)):
            logging.debug("In: Channel: %s - Name: %s - Value: %s %s", inputs[i]['channel'], query['series'][i]['name'], values[0][i+1], query['series'][i]['unit'])
            
            if self._sensors['sensors'].get("input_" + str(inputs[i]['channel']), None) is None:
                self._sensors['sensors']["input_" + str(inputs[i]['channel'])] = Sensor(inputs[i]['channel'], query['series'][i]['name'], "Input", query['series'][i]['unit'], values[0][i+1])
            else:
                inputsensor = self._sensors['sensors'].get("input_" + str(inputs[i]['channel']))
                inputsensor.setName(query['series'][i]['name'])
                inputsensor.setUnit(query['series'][i]['unit'])
                inputsensor.setValue(values[0][i+1])
                inputsensor.setSensorID(self._macAddress)

        for i in range(len(outputs)):
            logging.debug("Out: Name: %s - Value: %s %s", outputs[i]['name'], outputs[i]['units'], outputs[i]['value'])

            if self._sensors['sensors'].get("output_" + str(outputs[i]['name']), None) is None:
                self._sensors['sensors']["output_" + str(outputs[i]['name'])] = Sensor("N/A", outputs[i]['name'], "Output", outputs[i]['units'], outputs[i]['value'])
            else:
                outputsensor = self._sensors['sensors'].get("output_" + str(outputs[i]['name']))
                outputsensor.setUnit(outputs[i]['units'])
                outputsensor.setValue(outputs[i]['value'])
                outputsensor.setSensorID(self._macAddress)

    async def _getQueryShowSeries(self):
        url = "http://{}/query?show=series".format(self._ip)
        logging.debug("URL: %s", url)
        return await self._connection.get(url, self._username, self._password)

    async def _getQuerySelectSeries(self, sensor_names):
        url = "http://{}/query?select=[time.iso,".format(self._ip)
        delim = ","
        strSeries = delim.join(sensor_names)
        url = url + strSeries + "]&begin=s-5s&end=s&group=5s"
        return await self._connection.get(url, self._username, self._password)

