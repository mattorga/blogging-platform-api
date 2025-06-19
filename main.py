from typing import Annotated, List
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Depends
from sqlmodel import Field, SQLModel, create_engine, Session, select, JSON, or_

# SQLModels    
class Post(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str 
    content: str
    category: str
    tags: List[str] = Field(default_factory=list, sa_type=JSON)
    createdAt: datetime = Field(default_factory=datetime.now)
    updatedAt: datetime = Field(default_factory=datetime.now)

class PostCreate(SQLModel):
    title: str
    content: str
    category: str
    tags: List[str] = Field(default_factory=list, sa_type=JSON)

class PostUpdate(SQLModel):
    title: str
    content: str
    category: str
    tags: List[str] = Field(default_factory=list, sa_type=JSON)
    updatedAt: datetime = Field(default_factory=datetime.now)

# Database Connection
MYSQL_DATABASE = "blogging_platform_api"
DATABASE_URL = f"mysql+pymysql://root:Zeus_3245@localhost:3306/{MYSQL_DATABASE}"
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()

SessionDep = Annotated[Session, Depends(get_session)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

# FastAPI Instantiation
app = FastAPI(lifespan=lifespan)

## Path Operations
# CREATE
@app.post("/posts/")
def create_post(post: PostCreate, session: SessionDep):
    db_post = Post.model_validate(post)
    session.add(db_post)
    session.commit()
    session.refresh(db_post)
    return db_post

# READ
@app.get("/posts/")
async def read_posts(
    session: SessionDep,
    term: str | None = None
):
    stmt = select(Post)

    if term:
        stmt = stmt.where(
            or_(
                Post.title.icontains(term), # type: ignore
                Post.content.icontains(term), # type: ignore
                Post.category.icontains(term), # type: ignore
            )
        )

    posts = session.exec(stmt).all()
    return posts

@app.get("/posts/{post_id}")
async def read_post(
    session: SessionDep,
    post_id: int,
):
    post = session.get(Post, post_id)         
    return post

# UPDATE
@app.patch("/posts/{post_id}")
def update_post(
    session: SessionDep,
    post_id: int,
    post: PostUpdate
):
    post_db = session.get(Post, post_id)
    if not post_db:
        return {"error": "Post not found"}
    post_data = post.model_dump(exclude_unset=True)
    post_db.sqlmodel_update(post_data) # Error should already be handled
    session.add(post_db)
    session.commit()
    session.refresh(post_db)
    return post_db


# DELETE
@app.delete("/posts/{post_id}")
def delete_post(
    session: SessionDep,
    post_id: int
):
    post = session.get(Post, post_id)
    session.delete(post)
    session.commit()