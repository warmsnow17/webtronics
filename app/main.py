from fastapi import FastAPI

from app.api.endpoints import users, posts

from app.models.database import engine, Base

app = FastAPI()

app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(posts.router, prefix="/api", tags=["posts"])


Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5001)
