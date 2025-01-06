import uvicorn
from fastapi import FastAPI

from auth.routes import auth
from event.routes import event

app = FastAPI()
app.include_router(auth, prefix="/auth",tags=["auth"])
app.include_router(event, prefix="/event",tags=["event"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
