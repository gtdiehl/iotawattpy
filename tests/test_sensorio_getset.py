import pytest  # noqa: F401
import context  # noqa
from iotawattpy.sensorio import SensorIO  # noqa


@pytest.fixture(scope="session")
def sensor():
    sensor = SensorIO("myname", "")
    return sensor


def test_get_name(sensor):
    assert sensor.getName() == "myname"
