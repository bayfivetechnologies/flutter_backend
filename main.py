from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os

# ================= APP =================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= ROOT =================
@app.get("/")
def root():
    return {"message": "API is live"}

# ================= JWT CONFIG =================
SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_change_me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ================= USERS =================
users = {
    "vhw@test.com": {
        "email": "vhw@test.com",
        "password": "1234",
        "role": "village_health_worker"
    }
}

# ================= HELPERS =================
def authenticate_user(email, password):
    user = users.get(email)
    if not user:
        return None
    if user["password"] != password:
        return None
    return user

def create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ================= LOGIN =================
@app.post("/login")
def login(data: dict):
    email = data.get("email")
    password = data.get("password")

    user = authenticate_user(email, password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(
        {"sub": user["email"], "role": user["role"]},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"]
    }

# ================= AUTH =================
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {
            "email": payload.get("sub"),
            "role": payload.get("role")
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def require_vhw(user=Depends(get_current_user)):
    if user["role"] != "village_health_worker":
        raise HTTPException(status_code=403, detail="Forbidden")
    return user

# ================= ALERTS =================
@app.get("/alerts")
def alerts(user=Depends(require_vhw)):
    return {
        "alerts": [
            {
                "title": "Malaria Risk",
                "message": "High rainfall zone in Kariba (Mashonaland West). Increase mosquito net use and test suspected cases."
            },
            {
                "title": "Fever Spike",
                "message": "Rising fever cases across Mashonaland West. Monitor closely and refer severe cases."
            },
            {
                "title": "Diarrhea Cases",
                "message": "Increased cases in Chitungwiza. Encourage ORS and hygiene practices."
            }
        ],
        "total_patients": 120,
        "today_patients": 8
    }

# ================= TRIAGE LOGIC =================
@app.post("/assess")
def assess(data: dict, user=Depends(require_vhw)):
    symptoms = (data.get("symptoms") or "").lower()
    other = (data.get("other_symptoms") or "").lower()

    combined = symptoms + " " + other

    # ===== HIGH RISK =====
    if "difficulty breathing" in combined or "chest pain" in combined:
        return {
            "risk": "high",
            "advice": "URGENT: Refer patient to hospital immediately. Monitor airway and breathing."
        }

    # ===== MALARIA SUSPECT =====
    if "fever" in combined and "headache" in combined:
        return {
            "risk": "high",
            "advice": "Suspected malaria. Perform rapid test if available and refer to clinic immediately."
        }

    # ===== DIARRHEA =====
    if "diarrhea" in combined or "vomiting" in combined:
        return {
            "risk": "medium",
            "advice": "Give Oral Rehydration Salts (ORS), encourage fluids, monitor dehydration signs. Refer if condition worsens."
        }

    # ===== COUGH / GENERAL =====
    if "cough" in combined:
        return {
            "risk": "low",
            "advice": "Give paracetamol for fever or pain, advise rest and fluids. Monitor for 2–3 days."
        }

    # ===== DEFAULT =====
    return {
        "risk": "low",
        "advice": "Mild symptoms. Provide basic care (paracetamol, fluids, rest) and monitor patient."
    }

# ================= RENDER START =================
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
