from pydantic import BaseModel, Field


class ComposeServiceDefinition(BaseModel):
    name: str = Field(min_length=1)
    published_ports: tuple[int, ...] = ()


class StackDefinition(BaseModel):
    name: str = Field(min_length=1)
    compose_content: str = Field(min_length=1)
