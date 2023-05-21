import pydantic
import toml
from pathlib import Path


class QuickStartConfig(pydantic.BaseModel):
    name: str
    project_id: int
    task_id: int
    url: str | None
    notes: str | None


class Config(pydantic.BaseModel):
    token: str
    account_id: str
    user_id: str
    quickstart: list[QuickStartConfig]

    @classmethod
    def load(cls, path: Path):
        return cls(**toml.load(path))
