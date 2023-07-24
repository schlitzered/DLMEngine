from typing import get_args as typing_get_args
from typing import List
from typing import Literal
from typing import Optional
from pydantic import BaseModel
from pydantic import constr
from pydantic import StrictStr

from dlm_engine.model.common import MetaMulti

filter_literal = Literal[
    "id",
    "description",
]

filter_list = set(typing_get_args(filter_literal))

sort_literal = Literal["id"]
sort_order_literal = Literal[
    "ascending",
    "descending",
]


OrgId = constr(regex="([a-zA-Z0-9]{3,64})")
OrgIdAll = constr(regex="([a-zA-Z0-9]{3,64}|_all)")


class OrgGet(BaseModel):
    id: Optional[OrgId] = None
    description: Optional[StrictStr] = None


class OrgGetMulti(BaseModel):
    result: List[OrgGet]
    meta: MetaMulti


class OrgPost(BaseModel):
    description: Optional[StrictStr] = ""


class OrgPut(BaseModel):
    description: Optional[StrictStr] = None
