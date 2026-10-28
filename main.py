from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config.database import create_db_and_tables
from app.exceptions.app_exception import AppException
from app.routers.admin_router import router as admin_router
from app.routers.payment_router import router as payment_router
from app.routers.maintenance_request_router import router as maintenance_request_router
from app.routers.customer_router import router as customer_router
from app.routers.auth_router import router as auth_router
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import app.models
from sqlmodel import Session
from app.config.database import engine
from app.config.seed_admin import seed_admin



@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()

    with Session(engine) as session:
        seed_admin(session)

    yield


app = FastAPI(title="Car Maintenance System", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://motora-gamma.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


app.include_router(auth_router)
app.include_router(customer_router)
app.include_router(maintenance_request_router)
app.include_router(payment_router)
app.include_router(admin_router)

@app.get("/")
def home():
    return {"message": "Car Maintenance System API is running"}