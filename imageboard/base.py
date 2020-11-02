import asyncio
import copy
import typing as t

import aiohttp
import ujson

ListDict = t.TypeVar("ListDict", dict, list)


class ImageBoardException(Exception):
    pass


class UnknownRequestMethod(ImageBoardException):
    pass


class InvalidJsonData(ImageBoardException):
    pass


class ImageData(dict):
    """
    Based on: https://stackoverflow.com/a/32107024/13274776

    Example:
    m = ImageData({'first_name': 'Eduardo'}, last_name='Pool', age=24, sports=['Soccer'])
    """

    __setattr__ = dict.__setitem__  # type: ignore

    def __init__(self, dct):
        for key, value in dct.items():
            if hasattr(value, "keys"):
                value = ImageData(value)
            self[key] = value

    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError as ex:
            raise AttributeError(f"No attribute called: {name}") from ex

    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError as ex:
            raise AttributeError(f"No attribute called: {k}") from ex

    def export_data(self):
        return dict(self)


class ImageBoard:
    def __init__(self):
        self._sesi = aiohttp.ClientSession(headers={"User-Agent": "ihaBoard/1.0"})
        self.BASE_URL: str

        self._methods_maps = {
            "get": self._sesi.get,
            "post": self._sesi.post,
        }

    async def shutoff(self):
        await self._sesi.close()

    async def _request(self, method: str, path: str, **kwargs) -> t.Tuple[t.AnyStr, int, dict]:
        req_method = self._methods_maps.get(method.lower(), None)
        if req_method is None:
            raise UnknownRequestMethod(f"Method `{method}` are unknown.")
        async with req_method(f"{self.BASE_URL}/{path}", **kwargs) as resp:
            try:
                text_data = await resp.text()
            except Exception:
                text_data = await resp.read()
            status_code = resp.status
            headers_data = resp.headers

        return text_data, status_code, headers_data

    async def request_json(self, method: str, path: str, **kwargs) -> t.Tuple[t.Union[ListDict, str], int]:
        json_data, status, _ = await self._request(method, path, **kwargs)
        try:
            json_data = ujson.loads(json_data)
        except ValueError:
            raise InvalidJsonData
        return json_data, status

    async def parse_json(self, dataset: ListDict, mappings: dict) -> t.List[ImageData]:
        if isinstance(dataset, dict):
            dataset = [dataset]  # type: ignore

        async def _internal_map(main_data: dict) -> ImageData:
            mapped = copy.deepcopy(mappings)

            def _map_it(value):
                if isinstance(value, list):
                    collect_value = []
                    for val in value:
                        sep = None
                        if val and val.startswith("++"):
                            sep = val[2]
                            val = val[5:]
                        data_ = main_data[val]
                        if data_ is None:
                            collect_value.append("")
                            continue
                        if sep:
                            data_ = data_.split(sep)
                        collect_value.append(data_)
                    return collect_value
                else:
                    sep = None
                    if value.startswith("++"):
                        sep = value[2]
                        value = value[5:]
                    data_ = main_data[value]
                    if data_ is None:
                        return ""
                    if sep:
                        data_ = data_.split(sep)
                    return data_

            for key, value in mapped.items():
                if isinstance(value, dict):
                    for inner_key, inner_val in value.items():
                        mapped[key][inner_key] = _map_it(inner_val)
                else:
                    mapped[key] = _map_it(value)
            ib = ImageData(mapped)
            return ib  # type: ignore

        tasks_manager = [_internal_map(data) for data in dataset]
        final_dataset = []
        for tasks in asyncio.as_completed(tasks_manager):
            ib_data = await tasks
            final_dataset.append(ib_data)
        return final_dataset
