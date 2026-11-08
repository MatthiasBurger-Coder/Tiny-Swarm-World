from pydantic import BaseModel, ConfigDict, Field


class ComposeServiceDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)
    image_ref: str = ""
    published_ports: tuple[int, ...] = ()


class StackDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)
    compose_content: str = Field(min_length=1)


class StackConfigurationSnapshot(BaseModel):
    """Immutable selected Compose content, already validated by its repository."""

    model_config = ConfigDict(frozen=True)
    stacks: tuple[StackDefinition, ...]

    def get_compose_of(self, stack_name: str) -> StackDefinition:
        for stack in self.stacks:
            if stack.name == stack_name:
                return stack
        raise ValueError("Stack is not part of the validated configuration snapshot.")
