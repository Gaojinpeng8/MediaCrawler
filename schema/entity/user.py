from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserEntity(BaseModel):
    """用户实体：与 `database.models.User` 对应的传输对象。"""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    user_name: str
    pass_word: Optional[str] = None

    def to_dict(self) -> dict:
        return self.model_dump()