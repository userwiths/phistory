from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

import sqlite3

from poc import Manager
from models import *

app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:8001"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    manager = Manager()
    dashboard = manager.construct_dashboard()
    return dashboard

@app.get("/visits", response_model=VisitsPageResponse)
def get_visits(page:int = 0, limit:int = 10, sort:str = "date", dir:str = "asc") -> VisitsPageResponse:
    manager = Manager()
    result = manager.get_visits(page, limit, sort, dir)
    return result

@app.get("/visits/{visit_id}", response_model=Visit)
def get_visit(visit_id:int) -> Visit:
    manager = Manager()
    result = manager.get_visit(visit_id)
    return result

@app.get("/websites/actual", response_model=WebsitePageResponse)
def read_websites(page:int = 0, limit:int = 10, sort:str = "url", dir:str = "asc"):
    manager = Manager()
    result = manager.get_websites(page, limit, sort, dir, True)
    return result

@app.get("/websites", response_model=WebsitePageResponse)
def read_websites(page:int = 0, limit:int = 10, sort:str = "url", dir:str = "asc"):
    manager = Manager()
    result = manager.get_websites(page, limit, sort, dir)
    return result

@app.get("/websites/{visit_id}", response_model=Website)
def read_visit(visit_id:int):
    manager = Manager()
    result = manager.get_visit(visit_id)
    return result

@app.post("/websites", status_code=201)
def post_visit(url:str):
    manager = Manager()
    result = manager.post_visit(url)
    return result

@app.put("/websites/{visit_id}")
def put_visit(visit_id:int, comment:str = "", tag:str = ""):
    manager = Manager()
    result = manager.put_visit(visit_id, comment, tag)
    return result

@app.get("/queries")
def read_queries(page:int = 0, limit:int = 10, sort:str = "query", dir:str = "asc"):
    manager = Manager()
    result = manager.get_queries(page, limit, sort, dir)
    return result

@app.get("/metadata")
def read_metadata(page:int = 0, limit:int = 10, sort:str = "date", dir:str = "asc"):
    manager = Manager()
    result = manager.get_metadata(page, limit, sort, dir)
    return result

@app.get("/comments")
def read_comments(page:int = 0, limit:int = 10, sort:str = "date", dir:str = "asc"):
    manager = Manager()
    result = manager.get_comments(page, limit, sort, dir)
    return result

@app.get("/tags")
def read_tags(page:int = 0, limit:int = 10, sort:str = "tag", dir:str = "asc"):
    manager = Manager()
    result = manager.get_tags(page, limit, sort, dir)
    return result

@app.get("/search")
def search(query:str):
    manager = Manager()
    result = manager.search(query)
    return result

@app.get("/users")
def read_users(page:int = 0, limit:int = 10, sort:str = "name", dir:str = "asc"):
    manager = Manager()
    result = manager.get_users(page, limit, sort, dir)
    return result

@app.get("/users/{user_id}")
def read_user(user_id:int):
    manager = Manager()
    result = manager.get_user(user_id)
    return result

@app.post("/users", status_code=201)
def post_user(name:str):
    manager = Manager()
    result = manager.post_user(name)
    return result

@app.get("/groups")
def read_groups(page:int = 0, limit:int = 10, sort:str = "name", dir:str = "asc"):
    manager = Manager()
    result = manager.get_groups(page, limit, sort, dir)
    return result

@app.get("/groups/{group_id}")
def read_group(group_id:int):
    manager = Manager()
    result = manager.get_group(group_id)
    return result

@app.post("/groups", status_code=201)
def post_group(name:str):
    manager = Manager()
    result = manager.post_group(name)
    return result

@app.get("/media")
def read_media(page:int = 0, limit:int = 10, sort:str = "date", dir:str = "asc"):
    manager = Manager()
    result = manager.get_media(page, limit, sort, dir)
    return result