from fastapi import FastAPI
from routers.auth import router as auth_router
from db_config import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Register your router globally
app.include_router(auth_router)

@app.get("/")
def root():
    return {"message": "API is running"}