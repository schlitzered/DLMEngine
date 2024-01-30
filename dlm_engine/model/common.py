from pydantic import Field, BaseModel
from typing_extensions import Annotated


class MetaMulti(BaseModel):
    result_size: Annotated[int, Field(ge=0)]


class DataDelete(BaseModel):
    pass
