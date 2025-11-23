from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import requests

app = FastAPI()

users = {
    "diag":      {"password": "diag123",     "role": "Diag"},
    "admin":     {"password": "admin123",    "role": "Admin"},
    "superuser": {"password": "super123",    "role": "Superuser"},
}

app.mount("/webserver", StaticFiles(directory="webserver"), name="webserver")

@app.get("/")
def root():
    return RedirectResponse("/webserver/login/login.html")

@app.post("/api/login")
def login(username: str = Form(...), password: str = Form(...)):
    user = users.get(username.lower())
    if not user or user["password"] != password:
        return JSONResponse({"success": False, "message": "Hibás felhasználónév vagy jelszó"}, status_code=401)
    return {"success": True, "role": user["role"]}

@app.get("/api/status")
def proxy_status():
    try:
        r = requests.get("http://localhost:51200/api/status", timeout=0.5)
        return r.json()
    except Exception as e:
        return {"error": "Nem érhető el a Python backend", "details": str(e)}

if __name__ == "__main__":
    import uvicorn
    print("[WEB] Webserver indul: http://localhost:8000/")
    uvicorn.run(app, host="0.0.0.0", port=8000)
