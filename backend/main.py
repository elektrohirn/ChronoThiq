from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import users, projects, tasks

app = FastAPI(title="Netzplan App API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(projects.router)
app.include_router(tasks.router)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def root():
    return {"status": "Netzplan API läuft"}

@app.post("/login")
def login(username: str, password: str):
    from database import get_db
    from auth import authenticate_user, create_access_token
    db = next(get_db())
    user = authenticate_user(db, username, password)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Ungültige Anmeldedaten")
    token = create_access_token({"sub": user.username, "role": user.role})
    return {"access_token": token, "role": user.role, "user_id": user.id, "username": user.username}