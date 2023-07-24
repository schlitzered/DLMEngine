from typing import get_args as typing_get_args
from typing import List
from typing import Literal
from typing import Optional
from pydantic import BaseModel
from pydantic import StrictBool
from pydantic import EmailStr
from pydantic import StrictStr

from dlm_engine.model.common import MetaMulti

filter_literal = Literal[
    "id",
    "admin",
    "backend",
    "backend_ref",
    "email",
    "name",
]

filter_list = set(typing_get_args(filter_literal))

sort_literal = Literal[
    "id",
    "admin",
    "email",
    "name",
]
sort_order_literal = Literal[
    "ascending",
    "descending",
]


class UserGet(BaseModel):
    admin: Optional[StrictBool] = None
    email: Optional[EmailStr] = None
    name: Optional[StrictStr] = None
    id: Optional[StrictStr] = None
    backend: Optional[StrictStr] = None
    backend_ref: Optional[StrictStr] = None


class UserGetMulti(BaseModel):
    result: List[UserGet]
    meta: MetaMulti


class UserPost(BaseModel):
    admin: StrictBool = False
    email: EmailStr
    name: StrictStr
    password: StrictStr


class UserPut(BaseModel):
    admin: Optional[StrictBool] = None
    email: Optional[EmailStr] = None
    name: Optional[StrictStr] = None
    password: Optional[StrictStr] = None
