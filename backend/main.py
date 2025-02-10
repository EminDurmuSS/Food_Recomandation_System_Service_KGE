import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import recipe_info, recommend, unique_items

load_dotenv()

WORKER_COUNT = int(os.getenv("WORKER_COUNT", 1))

app = FastAPI(
    title="Food Recommendation API",
    version="1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommend.router)
app.include_router(unique_items.router)
app.include_router(recipe_info.router)


@app.get("/")
def root():
    return {"message": "Hello! This is the new KG-based Food Recommendation API."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, workers=WORKER_COUNT)
