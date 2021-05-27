import logging

import httpx

GET = "get"
POST = "post"

LOGGER = logging.getLogger(__name__)


class Connection:
    def __init__(self, websession: httpx.AsyncClient, host):
        self._host = host
        self._series = []
        self._websession = websession

    async def get(self, url, username=None, password=None):
        return await self.__open(url, username=username, password=password)

    async def __open(
        self,
        url,
        method=GET,
        headers=None,
        params=None,
        baseurl="",
        decode_json=True,
        auth=None,
        username=None,
        password=None,
    ):
        if username is not None:
            auth = httpx.DigestAuth(username, password)

        LOGGER.debug("URL: %s", url)
        try:
            resp = await getattr(self._websession, method)(
                url, headers=headers, params=params, auth=auth
            )
            # TODO Commenting out this check as the IoTaWatt is returning 'text/json'and will have to wait until this is resolved
            # if decode_json:
            #    return (await resp.json())
            return resp
        except httpx.HTTPError as err:
            LOGGER.error("Err: %s", err)
