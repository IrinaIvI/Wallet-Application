from fastapi import FastAPI
from app.routers import router

app = FastAPI(title='Wallet App')

app.include_router(router)