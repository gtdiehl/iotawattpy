import logging

import aiohttp

_LOGGER = logging.getLogger(__name__)

GET = "get"
POST = "post"


class Connection:

    def __init__(self, websession: aiohttp.ClientSession, host):
        self._host = host
        self._series = []
        self._websession = websession

    async def connect(self):
        await self._refresh_series()
        return self._series

    async def _refresh_series(self):
        url = "http://{}/query?show=series".format(self._host)
        js_resp = await self.get(url)
        self._series = js_resp["series"]

    async def get(self, url):
        return await self.__open(url)

    async def __open(
        self, url, method=GET, headers=None, data=None,
        json_data=None, params=None, baseurl="", decode_json=True,
    ):

        _LOGGER.debug("URL: %s", url)
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
