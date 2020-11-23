import logging

_LOGGER = logging.getLogger(__name__)


class SensorIO():

    def __init__(self, name, unit):
        self._name = name
        self._unit = unit
        self._value = None

    def getName(self):
        return self._name

    def getUnit(self):
        return self._unit

    def setUnit(self, unit):
        self._unit = unit

    def getValue(self):
        return self._value

    def setValue(self, value):
        self._value = value
