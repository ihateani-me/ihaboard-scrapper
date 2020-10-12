import typing as t
from .base import ImageBoard


class Danbooru(ImageBoard):
    def __init__(self, safe_version=False):
        super().__init__()
        self.BASE_URL = "https://danbooru.donmai.us"
        self._family_friendly = safe_version
        self._mappings = {
            "id": "id",
            "title": "tag_string_character",
            "tags": "++ ++tag_string",
            "meta": "++ ++tag_string_meta",
            "artist": "++ ++tag_string_artist",
            "source": "source",
            "thumbnail": "preview_file_url",
            "image_url": "file_url",
            "image_info": {"w": "image_width", "h": "image_height", "e": "file_ext", "s": "file_size"},
        }

    async def search(self, query_tags: t.List[str] = []) -> t.Dict[str, object]:
        params: t.Dict[str, t.Union[str, int]] = {
            "limit": 10,
        }
        if self._family_friendly:
            redone_tags = []
            for tag in query_tags:
                if "rating:" in tag:
                    continue
                redone_tags.append(tag)
            redone_tags.append("rating:safe")
        query_tags = [tag for tag in query_tags if tag]
        if query_tags:
            params["tags"] = "+".join(query_tags)
        print(params["tags"])
        results, status_code = await self.request_json("get", "posts.json", params=params)
        if status_code == 200:
            parsed_data = await self.parse_json(results, self._mappings)  # noqa: E501
            results_final = {
                "results": parsed_data,
                "total_data": len(parsed_data),
                "parser": "danbooru",
                "status_code": 200,
            }
        else:
            results_final = {
                "results": [],
                "total_data": 0,
                "message": "error occured.",
                "status_code": status_code,
            }
        return results_final

    async def random_search(self, query_tags: t.List[str] = []) -> t.Dict[str, object]:
        query_tags = [tag.lower() for tag in query_tags]
        if "order:random" not in query_tags:
            query_tags.append("order:random")
        results = await self.search(query_tags)
        return results
