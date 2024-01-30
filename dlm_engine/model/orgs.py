from typing import get_args as typing_get_args
from typing import List
from typing import Literal
from typing import Optional
from pydantic import StringConstraints, BaseModel
from pydantic import StrictStr

from dlm_engine.model.common import MetaMulti
from typing_extensions import Annotated

filter_literal = Literal[
    "id",
    "description",
]

filter_list = list(set(typing_get_args(filter_literal)))

sort_literal = Literal["id"]
sort_order_literal = Literal[
    "ascending",
    "descending",
]


OrgId = Annotated[str, StringConstraints(pattern="([a-zA-Z0-9]{3,64})")]
OrgIdAll = Annotated[str, StringConstraints(pattern="([a-zA-Z0-9]{3,64}|_all)")]


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
