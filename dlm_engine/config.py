import typing

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

log_levels = typing.Literal[
    "CRITICAL", "FATAL", "ERROR", "WARN", "WARNING", "INFO", "DEBUG"
]


class Ldap(BaseModel):
    url: typing.Optional[str] = None
    binddn: typing.Optional[str] = None
    password: typing.Optional[str] = None


class OAuthClient(BaseModel):
    id: str
    secret: str


class OAuthUrl(BaseModel):
    authorize: str
    accesstoken: str
    userinfo: typing.Optional["str"] = None


class OAuth(BaseModel):
    scope: str
    type: str
    client: OAuthClient
    url: OAuthUrl


class Mongodb(BaseModel):
    url: str = "mongodb://localhost:27017"
    database: str = "dlm_engine"


class App(BaseModel):
    loglevel: log_levels = "INFO"
    secretkey: str = ""


class Settings(BaseSettings):
    app: App = App()
    ldap: Ldap = Ldap()
    mongodb: Mongodb = Mongodb()
    oauth: dict[str, OAuth] = dict()
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="_")
    # model_config = SettingsConfigDict(env_file=".env")
