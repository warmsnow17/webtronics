from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String)
    external_data = Column(Text)
    posts = relationship("Post", back_populates="author")
    likes = relationship("Like", back_populates="user")
