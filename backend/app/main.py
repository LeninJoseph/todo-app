import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Make the project root importable so `import config` finds ../../config
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI

from db import models  # noqa: F401  (registers tables on Base.metadata)
from db.db import Base, engine
from routers import auth, users




@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)  # creates missing tables only
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)
app.include_router(users.router)


@app.get('/')
def root():
    return "Hello Lenin!"


if __name__ == "__main__":
    root()
