from iotawattpy import Iotawatt, Connection
from aiohttp import ClientSession
import logging
import asyncio

LOOP = asyncio.get_event_loop()

logging.basicConfig(level='DEBUG')

class Tester:

    def __init__(self, host):
        self._host = host

    async def run(self):
        self.session = ClientSession()
        self.iotawatt = Iotawatt("iotawatt", self._host, self.session)
        await self.iotawatt.update()
        a = self.iotawatt.getSensors()
        await self.session.close()

        for i in range(len(a)):
            logging.info("%s is consuming %s %s", 
                a[i].getName(), a[i].getValue(), a[i].getUnit())

def main():

    logging.info('Started')

    test = Tester("10.0.20.202")
    LOOP.run_until_complete(test.run())

if __name__ == "__main__":
    main()