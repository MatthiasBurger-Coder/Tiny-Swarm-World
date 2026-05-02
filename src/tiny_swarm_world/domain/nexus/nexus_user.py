from pydantic import BaseModel, ConfigDict, Field


class NexusUser(BaseModel):
    model_config = ConfigDict(extra="allow")

    userId: str = Field(min_length=1)
    firstName: str | None = None
    lastName: str | None = None
    emailAddress: str | None = None
    source: str | None = None
    status: str = Field(default="active")
    readOnly: bool | None = None
    roles: list[str] = Field(default_factory=list)
