from typing import Union

from fastapi import APIRouter

test = APIRouter()


@test.get("/")
async def root():
    return {"message": "Hello World"}


@test.get("/items/{item_id}")
async def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
