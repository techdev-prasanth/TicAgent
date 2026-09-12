from fastapi import FastAPI
from routers.auth import router as auth_router
from routers.users import router as users_router
from ai_modules.apis import router as ai_router
from db_config import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Register your router globally
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(ai_router)

@app.get("/")
def root():
    return {"message": "API is running"}