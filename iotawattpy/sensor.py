import logging

LOGGER = logging.getLogger(__name__)


class Sensor:
    def __init__(
        self,
        channel,
        base_name,
        suffix,
        io_type,
        unit,
        value,
        begin,
        mac_addr,
        fromStart=False,
    ):
        self._channel = channel
        self._base_name = base_name
        self._suffix = suffix
        self._type = io_type
        self._unit = unit
        self._value = value
        self._begin = begin
        self._sensor_id = None
        self._fromStart = fromStart

        self.hub_mac_address = mac_addr

        self.setSensorID(mac_addr)

    def getChannel(self):
        return self._channel

    def setChannel(self, channel):
        self._channel = channel

    def getSensorID(self):
        return self._sensor_id

    def setSensorID(self, hub_mac_address):
        self._sensor_id = hub_mac_address + "_" + self._type + "_" + self.getName()

    def getSourceName(self):
        return self._base_name + (f"{self._suffix}" if self._suffix != None else "")

    def getName(self):
        return self.getSourceName() + ("_last" if self._suffix == ".wh" and not self._fromStart else "")

    def getBaseName(self):
        return self._base_name

    def setBaseName(self, base_name):
        self._base_name = base_name

    def getSuffix(self):
        return self._suffix

    def setSuffix(self, suffix):
        self._suffix = suffix

    def getType(self):
        return self._type

    def setType(self, io_type):
        self._type = io_type

    def getUnit(self):
        return self._unit

    def setUnit(self, unit):
        self._unit = unit

    def getValue(self):
        return self._value

    def setValue(self, value):
        self._value = value

    def getBegin(self):
        return self._begin

    def setBegin(self, begin):
        self._begin = begin

    def getFromStart(self):
        return self._fromStart

    def setFromStart(self, fromStart):
        self._fromStart = fromStart
