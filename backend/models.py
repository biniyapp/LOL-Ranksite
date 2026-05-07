from sqlalchemy import Column, Integer, String, Float, UniqueConstraint
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String, index=True)
    tag = Column(String, index=True)
    score = Column(Integer, default=0)

    __table_args__ = (UniqueConstraint('nickname', 'tag', name='_nickname_tag_uc'),)
