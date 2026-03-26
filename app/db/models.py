from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(255))

class Domain(Base):
    __tablename__ = "domains"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(45))
    subdomain = Column(String(100), unique=True, index=True)
    content = Column(String(45))
    cloudflare_id = Column(String(100))  # <-- 이 줄을 추가하세요!
    owner_id = Column(Integer, ForeignKey("users.id"))
    priority = Column(Integer, nullable=True)

    # ★ 핵심: '이름'과 '타입'의 세트가 중복되지 않게 설정 ★
    __table_args__ = (
        UniqueConstraint('subdomain', 'type', name='_subdomain_type_uc'),
    )