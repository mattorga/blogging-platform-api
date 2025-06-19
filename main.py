from typing import Annotated, List
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Depends
from sqlmodel import Field, SQLModel, create_engine, Session, select, JSON

# SQLModels    
class Post(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str 
    content: str
    category: str
    tags: List[str] = Field(default_factory=list, sa_type=JSON)
    createdAt: datetime = Field(default_factory=datetime.now)
    updatedAt: datetime 

class PostCreate(SQLModel):
    title: str
    content: str
    category: str
    tags: List[str] = Field(default_factory=list, sa_type=JSON)

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
# GET
@app.get("/posts/")
async def read_posts(
    session: SessionDep,
):
    posts = session.exec(select(Post)).all()
    return posts


# POSTS
@app.post("/posts/")
def create_post(post: PostCreate, session: SessionDep):
    db_post = Post.model_validate(post)
    session.add(db_post)
    session.commit()
    session.refresh(db_post)
    return db_post
