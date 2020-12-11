from iotawattpy.iotawatt import Iotawatt
from aiohttp import ClientSession
import logging
import asyncio
import time

LOOP = asyncio.get_event_loop()

logging.basicConfig(level='DEBUG')


class Tester:

    def __init__(self, host):
        self._host = host

    async def run(self):
        self.session = ClientSession()
        self.iotawatt = Iotawatt("iotawatt", self._host, self.session)
        while(True):
            logging.info("=============================================")
            await self.iotawatt.update()
            logging.info("=============================================")
            time.sleep(5)            


def main():

    logging.info('Started')

    test = Tester("10.0.20.202")
    LOOP.run_until_complete(test.run())


if __name__ == "__main__":
    main()
