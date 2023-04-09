from sqlalchemy import Integer, Column, String, ForeignKey

from . import Base


class Dialog(Base):
    __tablename__ = "dialogs"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    user_1: int = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    user_2: int = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

    def __repr__(self) -> str:
        return f"<Dialog id={self.id} users=[{self.user_1}, {self.user_2}]>"

    def other_user(self, current_user_id: int) -> int:
        return self.user_1 if current_user_id == self.user_2 else self.user_2


class Message(Base):
    __tablename__ = "messages"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    dialog_id: int = Column(Integer, ForeignKey("dialogs.id", ondelete="CASCADE"))
    author_id: int = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    created_at: int = Column(Integer)
    text: str = Column(String)

    def __repr__(self) -> str:
        return f"<Message id={self.id} dialog_id={self.dialog_id} author={self.author} text={self.text[:16]}>"