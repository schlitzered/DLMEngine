from datetime import datetime
from typing import get_args as typing_get_args
from typing import List
from typing import Literal
from typing import Optional
from pydantic import BaseModel
from pydantic import StrictStr

from dlmengine.model.v2.common import ModelV2MetaMulti

filter_literal = Literal[
    "id",
    "acquired_by",
    "acquired_since",
]

filter_list = set(typing_get_args(filter_literal))

sort_literal = Literal["id",]


class ModelV2LockGet(BaseModel):
    id: Optional[StrictStr] = None
    acquired_by: str
    acquired_since: datetime


class ModelV2LockGetMulti(BaseModel):
    result: List[ModelV2LockGet]
    meta: ModelV2MetaMulti


class ModelV2LockPost(BaseModel):
    acquired_by: str
