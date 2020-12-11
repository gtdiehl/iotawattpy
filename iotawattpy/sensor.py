import logging

_LOGGER = logging.getLogger(__name__)


class Sensor:
    def __init__(self, channel, name, io_type, unit, value):
        self._channel = channel
        self._name = name
        self._type = io_type
        self._unit = unit
        self._value = value

    def getChannel(self):
        return self._channel

    def setChannel(self, channel):
        self._channel = channel

    def getName(self):
        return self._name

    def setName(self, name):
        self._name = name
        
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
