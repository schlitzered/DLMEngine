from datetime import datetime
from typing import get_args as typing_get_args
from typing import List
from typing import Literal
from typing import Optional
from pydantic import BaseModel
from pydantic import StrictStr

filter_literal = Literal[
    "id",
    "acquired_by",
    "acquired_since",
]

filter_list = set(typing_get_args(filter_literal))

sort_literal = Literal["id",]


class ModelV1LockGet(BaseModel):
    id: Optional[StrictStr] = None
    acquired_by: str
    acquired_since: datetime


class ModelV1LockGetData(BaseModel):
    data: ModelV1LockGet


class ModelV1LockGetMultiResults(BaseModel):
    results: List[ModelV1LockGetData]


class ModelV1LockGetMultiResultsData(BaseModel):
    data: ModelV1LockGetMultiResults


class ModelV1LockPost(BaseModel):
    acquired_by: str


class ModelV1LockPostData(BaseModel):
    data: ModelV1LockPost
