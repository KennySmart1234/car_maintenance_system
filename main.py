from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config.database import create_db_and_tables
from app.exceptions.app_exception import AppException
from app.routers.auth_router import router as auth_router


app = FastAPI(title="Car Maintenance System")


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=409,
        content={"detail": exc.message},
    )


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


app.include_router(auth_router)


@app.get("/")
def home():
    return {"message": "Car Maintenance System API is running"}