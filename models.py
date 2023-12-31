from typing import List
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_login import UserMixin
from database import Base


# Configure Tables
class User(UserMixin, Base):
    __tablename__ = "user_table"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(1000), nullable=False)
    posts: Mapped[List["BlogPost"]] = relationship(back_populates="author")
    comments: Mapped[List["Comment"]] = relationship(back_populates="author")

    def __repr__(self):
        return f"<User {self.id}>"


class BlogPost(Base):
    __tablename__ = "blog_post_table"

    id: Mapped[int] = mapped_column(primary_key=True)
    author: Mapped['User'] = relationship(back_populates="posts")
    author_id: Mapped[int] = mapped_column(ForeignKey('user_table.id'))

    title: Mapped[str] = mapped_column(String(250), nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

    comments: Mapped[List["Comment"]] = relationship(back_populates="post")

    def __repr__(self):
        return f"<Post {self.id}>"


class Comment(Base):
    __tablename__ = "comment_table"

    id: Mapped[int] = mapped_column(primary_key=True)
    author: Mapped['User'] = relationship(back_populates="comments")
    author_id: Mapped[int] = mapped_column(ForeignKey('user_table.id'))
    post: Mapped['BlogPost'] = relationship(back_populates="comments")
    post_id: Mapped[int] = mapped_column(ForeignKey('blog_post_table.id'))
    text: Mapped[str] = mapped_column(Text, nullable=False)


    def __repr__(self):
        return f"<Comment {self.id}>"
