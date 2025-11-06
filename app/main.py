from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import accounts, transactions

app = FastAPI(
    title="Banking System API",
    description="FastAPI Banking System converted from Django",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounts.router)
app.include_router(transactions.router)


@app.get("/")
def root():
    return {
        "message": "Banking System API",
        "version": "2.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
