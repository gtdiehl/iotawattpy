from sensorio import SensorIO
import aiohttp
import logging
from connection import Connection

_LOGGER = logging.getLogger(__name__)

class Iotawatt:
    
    """Creates an Iotawatt object that represents the physical hardware"""
    """with sensors connected to it"""
    def __init__(self, name, ip, websession: aiohttp.ClientSession):
        self._name = name
        self._ip = ip
        self._sensors = []

        self._connection = Connection(websession, self._ip)

    """Retrieves sensor data and updates the Sensor objects"""
    async def update(self):
        seriesResponse = await self._getQueryShowSeries()
        self._setSensors(self._parseShowSeriesResponse(seriesResponse))
        await self._setValues()

    async def _getQueryShowSeries(self):
        url = "http://{}/query?show=series".format(self._ip)
        return await self._connection.get(url)

    def _parseShowSeriesResponse(self, response):
        series = dict()
        for i in range(len(response["series"])):
            series[response["series"][i]["name"]] = response["series"][i]["unit"]
        return series

    def _setSensors(self, series):
        for i in series:
            self._sensors.append(SensorIO(i, series[i]))

    async def _setValues(self):
        values = self._parseSelectSeriesResponse(await self._getQuerySelectSeries())
        for i in range(len(self._sensors)):
            self._sensors[i].setValue(values[i])

    def _parseSelectSeriesResponse(self, response):
        response = response.pop(0)
        last_update = response.pop(0)
        return response

    async def _getQuerySelectSeries(self):
        url = "http://{}/query?select=[time.iso,".format(self._ip)
        delim = ","
        names = []
        for i in range(len(self._sensors)):
            names.append(self._sensors[i].getName())
        strSeries = delim.join(names)
        url = url + strSeries + "]&begin=s-5s&end=s&group=5s"
        return await self._connection.get(url)

    """Returns an array of SensorIO objects"""
    def getSensors(self):
        return self._sensors