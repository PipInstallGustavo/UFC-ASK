from fastapi import FastAPI
from interface.api import routes 

app = FastAPI()

app.include_router(routes.router)
