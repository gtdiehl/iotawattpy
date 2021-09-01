import context  # noqa
import pytest  # noqa: F401

from iotawattpy.sensor import Sensor  # noqa


@pytest.fixture(scope="session")
def sensor():
    sensor = Sensor("", "myname", "", "Input", "Watts", 102, "2021-01-01", "deadbeef")
    return sensor


def test_get_name(sensor):
    assert sensor.getName() == "myname"
