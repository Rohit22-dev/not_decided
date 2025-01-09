import uvicorn
from fastapi import FastAPI

from auth.routes import auth
from event.routes import event
from tickets.routes import ticket

app = FastAPI()
app.include_router(auth, prefix="/auth", tags=["auth"])
app.include_router(event, prefix="/event", tags=["event"])
app.include_router(ticket, prefix="/tickets", tags=["tickets"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
