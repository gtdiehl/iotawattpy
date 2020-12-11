import pytest  # noqa: F401
import context  # noqa
from iotawattpy.sensor import Sensor  # noqa


@pytest.fixture(scope="session")
def sensor():
    sensor = Sensor("", "myname", "Input", "Watts", 102)
    return sensor


def test_get_name(sensor):
    assert sensor.getName() == "myname"
