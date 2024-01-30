from datetime import datetime
from typing import get_args as typing_get_args
from typing import List
from typing import Literal
from typing import Optional
from pydantic import StringConstraints, BaseModel
from pydantic import StrictStr

from dlm_engine.model.common import MetaMulti
from dlm_engine.model.orgs import OrgId
from typing_extensions import Annotated

filter_literal = Literal[
    "id",
    "org",
    "description",
    "disabled",
    "meta",
    "org",
    "package_name",
    "tags",
]

filter_list = set(typing_get_args(filter_literal))

sort_literal = Literal["id"]
sort_order_literal = Literal[
    "ascending",
    "descending",
]


OrgLockId = Annotated[str, StringConstraints(pattern="^([a-zA-Z0-9]+(|_))*$")]


class OrgLockDelete(BaseModel):
    acquired_by: Optional[StrictStr] = None
    force: Optional[bool] = None
    secret: Optional[StrictStr] = None


class OrgLockGet(BaseModel):
    id: Optional[OrgLockId] = None
    org: Optional[OrgId] = None
    acquired_by: Optional[StrictStr] = None
    acquired_since: Optional[datetime] = None
    secret: Optional[StrictStr] = None


class OrgLockGetMulti(BaseModel):
    result: List[OrgLockGet]
    meta: MetaMulti


class OrgLockPost(BaseModel):
    acquired_by: Optional[StrictStr] = None
    secret: Optional[StrictStr] = None
