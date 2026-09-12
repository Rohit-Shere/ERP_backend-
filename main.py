import uvicorn

from backend.app.main import app
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],   # GET, POST, PUT, DELETE, OPTIONS
    allow_headers=["*"],
)

def main() -> None:
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
