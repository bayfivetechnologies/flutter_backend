from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS (this is NON-NEGOTIABLE for Flutter)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # we tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "API is live"}