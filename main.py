import os, base64, random, string
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import httpx

from database import SessionLocal, engine, Base
from models import Email, Attachment

UPLOAD_DIR = "attachments"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()
Base.metadata.create_all(bind=engine)

# static
app.mount("/attachments", StaticFiles(directory=UPLOAD_DIR), name="attachments")
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

CF_API_TOKEN = os.getenv("CF_API_TOKEN")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")

# ===== Helpers =====
def gen_prefix(n=8):
    import secrets, string
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(n))

# ===== Webhook from Worker =====
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    db: Session = SessionLocal()

    email = Email(
        email_to=data.get("to"),
        subject=data.get("subject"),
        sender=data.get("from"),
        body_text=data.get("body_text"),
        body_html=data.get("body_html"),
        date=datetime.fromisoformat(data.get("date").replace("Z", "+00:00")) if data.get("date") else datetime.utcnow(),
    )
    db.add(email)
    db.commit()
    db.refresh(email)

    for att in data.get("attachments", []):
        filename = att.get("filename") or f"file_{email.id}"
        try:
            filedata = base64.b64decode(att.get("content") or "")
        except Exception:
            filedata = b""
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(filedata)
        db.add(Attachment(filename=filename, filepath=f"/attachments/{filename}", email_id=email.id))

    db.commit()
    db.close()
    return {"status": "ok", "id": email.id}

# ===== Cloudflare Domains =====
@app.get("/api/domains")
async def api_domains():
    if not CF_API_TOKEN or not CF_ACCOUNT_ID:
        return {"domains": ["yasir.id"]}
    headers = {"Authorization": f"Bearer {CF_API_TOKEN}"}
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/email/routing/domains"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=headers, timeout=15)
        data = r.json()
    if not data.get("success"):
        return {"domains": ["yasir.id"]}
    domains = [d["name"] for d in data["result"] if d.get("status") == "active"]
    return {"domains": domains or ["yasir.id"]}

# ===== Email select/generate =====
@app.get("/api/new")
async def api_new():
    # pick first domain from CF or fallback
    domains = (await api_domains())["domains"]
    domain = domains[0]
    return {"email": f"{gen_prefix()}@{domain}"}

@app.post("/api/custom")
async def api_custom(address: str = Form(...)):
    # trust client-provided full address
    return {"email": address}

@app.get("/api/inbox/{address}")
async def api_inbox(address: str):
    db: Session = SessionLocal()
    rows = db.query(Email).filter(Email.email_to == address).order_by(Email.date.desc()).all()
    out = []
    for e in rows:
        out.append({
            "id": e.id,
            "from": e.sender,
            "subject": e.subject,
            "date": e.date.isoformat(),
            "body_text": e.body_text,
            "body_html": e.body_html,
            "attachments": [{"filename": a.filename, "url": a.filepath} for a in e.attachments]
        })
    db.close()
    return out

# Root UI (optionally with path email)
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/{email}", response_class=HTMLResponse)
async def by_email(email: str, request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "initial_email": email})
