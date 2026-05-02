from pydantic import BaseModel, Field


class StackDefinition(BaseModel):
    name: str = Field(min_length=1)
    compose_content: str = Field(min_length=1)
