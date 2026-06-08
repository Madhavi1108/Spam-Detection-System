import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# import environment config
from backend.config import FRONTEND_URL, BASE_URL, PORT

app = FastAPI(title="Spam Detection System")


# ── CORS setup (uses env variable) ─────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    FRONTEND_URL,
    os.getenv("FRONTEND_DEV_URL", "http://localhost:8000"),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Basic health check ─────────────────────────────────────────
@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Spam Detection API is running",
        "base_url": BASE_URL,
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


# ── Optional: run directly ─────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=PORT, reload=True)
