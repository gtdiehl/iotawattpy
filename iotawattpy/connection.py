import logging

import aiohttp

GET = "get"
POST = "post"


class Connection:

    def __init__(self, websession: aiohttp.ClientSession, host):
        self._host = host
        self._series = []
        self._websession = websession

    async def get(self, url):
        return await self.__open(url)

    async def __open(
        self, url, method=GET, headers=None, data=None,
        json_data=None, params=None, baseurl="", decode_json=True,
    ):

        logging.debug("URL: %s", url)
        try:
            resp = await getattr(self._websession, method)(
                url, headers=headers, params=params, data=data, json=json_data
            )
            #TODO Commenting out this check as the IoTaWatt is returning 'text/json'and will have to wait until this is resolved
            #if decode_json:
            #    return (await resp.json())
            return resp
        except aiohttp.ClientResponseError as err:
            logging.error("Err: %s", err)
        except aiohttp.ClientConnectionError as err:
            logging.error("Err: %s", err)
