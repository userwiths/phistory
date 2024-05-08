from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    id: int
    name: str

class Media(BaseModel):
    website_id: int
    media_link: Optional[str]
    alt_text: Optional[str]
    is_cached: bool

class Metadata(BaseModel):
    website_id: int
    attribute_name: str|None
    attribute_id: int|None
    identifier: str|None
    identifier_name: str|None
    attribute: str|None
    attribute_value: str|None

class Comment(BaseModel):
    website_id: int
    comment: str
    date: str

class Tag(BaseModel):
    website_id: int
    tag: str

class Link(BaseModel):
    website_id: int
    destination_id: Optional[int]
    link: Optional[str]
    destination: str

class Query(BaseModel):
    website_id: int
    query: str

class Website(BaseModel):
    website_id: int
    url: str
    base_website: str|None
    times_visited: int
    last_visit: str
    actually_visited: bool
    metadata: Optional[list[Metadata]] = []
    queries: Optional[list[Query]] = []
    links: Optional[list[Link]] = []
    media: Optional[list[Media]] = []
    comments: Optional[list[Comment]] = []
    tags: Optional[list[Tag]] = []

class Paging(BaseModel):
    page: int = 0
    limit: int = 10
    sort: str = "date"
    dir: str = "desc"
    total: int = 0

class WebsitePageResponse(BaseModel):
    paging: Paging
    data: list[Website] = []

class QueryPageResponse(BaseModel):
    paging: Paging
    data: list[Query] = []

class MetadataPageResponse(BaseModel):
    paging: Paging
    data: list[Metadata] = []

class CommentPageResponse(BaseModel):
    paging: Paging
    data: list[Comment] = []

class TagPageResponse(BaseModel):
    paging: Paging
    data: list[Tag]
