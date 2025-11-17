from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import RedirectResponse

from routes import auth
from routes import user
from routes import ml_models
from routes import chat
from routes import assisstant

import logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(ml_models.router)
app.include_router(chat.router)
app.include_router(assisstant.router)

@app.exception_handler(StarletteHTTPException)
async def custom_404_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    return HTMLResponse(f"Error {exc.status_code}: {exc.detail}", status_code=exc.status_code)

