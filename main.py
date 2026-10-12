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

import app.models  # noqa: F401  (makes sure every table is registered)


app = FastAPI(title="Car Maintenance System")


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Car Maintenance System", lifespan=lifespan)


app.include_router(auth_router)
app.include_router(customer_router)
app.include_router(maintenance_request_router)
app.include_router(payment_router)
app.include_router(admin_router)

@app.get("/")
def home():
    return {"message": "Car Maintenance System API is running"}