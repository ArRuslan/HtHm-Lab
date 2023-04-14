from sqlalchemy import Integer, Column, String, ForeignKey

from . import Base


class User(Base):
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    login: str = Column(String, unique=True, nullable=False)
    password: str = Column(String, nullable=False)
    avatar: str = Column(String, nullable=True, default=None)

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, login={self.login!r}, avatar={self.avatar!r})"


class Session(Base):
    __tablename__ = "sessions"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    user_id: int = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

    def __repr__(self) -> str:
        return f"Session(id={self.id!r}, user_id={self.user_id!r})"