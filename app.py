from sanic import Sanic
from sanic.response import json
from ibapi.danbooru import Danbooru

app = Sanic("naotimes-ib")
app.config.FORWARDED_HOST = "poggers_in_chat"


def to_real_bool(string):
    bool_map = {
        "0": False,
        "1": True,
        "true": True,
        "false": False,
        "y": True,
        "n": False,
        "yes": True,
        "no": False,
        0: False,
        1: True,
        True: True,
        False: False,
    }
    if isinstance(string, str):
        string = string.lower()
    return bool_map.get(string, False)


@app.get("/danbooru")
async def danbooru_requests(request):
    params = request.args
    tags = params.get("search", "")
    do_random_search = to_real_bool(params.get("random", "0"))
    tags = [t for t in tags.split("+")]
    dbi = Danbooru(False)
    if do_random_search:
        results = await dbi.random_search(tags)
    else:
        results = await dbi.search(tags)
    await dbi.shutoff()
    return json(results, ensure_ascii=False, encode_html_chars=True, escape_forward_slashes=False, indent=4)


@app.get("/safebooru")
async def safebooru_request(request):
    params = request.args
    tags = params.get("search", "")
    do_random_search = to_real_bool(params.get("random", "0"))
    tags = [t for t in tags.split("+")]
    dbi = Danbooru(True)
    if do_random_search:
        results = await dbi.random_search(tags)
    else:
        results = await dbi.search(tags)
    await dbi.shutoff()
    return json(results, ensure_ascii=False, encode_html_chars=True, escape_forward_slashes=False, indent=4)


if __name__ == "__main__":
    app.run("127.0.0.1", 6969, debug=True, access_log=True, auto_reload=True)
