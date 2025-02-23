from sqlmodel import Field, SQLModel, create_engine

class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    age: int | None = Field(default=None, index=True)
    email: str = Field(index=True, unique=True)
    password: str = Field()

class Movies(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    genre: str = Field(index=True)
    provider: str = Field(default=None)

class Likes(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int
    movie_id: int | None = Field(default=None)

class Recommendations(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int
    movie_id: int | None = Field(default=None)
    rating: int | None = Field(default=None)