from typing import Optional

from pydantic import BaseModel

class DomainCreate(BaseModel):
    subdomain: str
    content: str
    type:str
    priority: Optional[int] = None


class DomainResponse(DomainCreate):
    id: int
    owner_id: int
    class Config:
        from_attributes = True

# 수정 시 사용 (PUT) - 모든 필드를 선택사항으로 두어 부분 수정 가능하게 함
class DomainUpdate(BaseModel):
    subdomain: Optional[str] = None
    type: Optional[str] = None
    content: Optional[str] = None
    priority: Optional[int] = None
