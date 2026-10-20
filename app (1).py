"""BIG BULL COPY — client registration/admin approval only, NO trade execution."""
import html
import os
import secrets
import hmac
from datetime import datetime, timezone
from urllib.parse import quote
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, DateTime, select, func
from sqlalchemy.orm import declarative_base, Session

DB_URL = os.environ.get('DATABASE_URL', 'sqlite:///./registrations.db')
if DB_URL.startswith('postgres://'):
    DB_URL = 'postgresql+psycopg://' + DB_URL[len('postgres://'):]
elif DB_URL.startswith('postgresql://'):
    DB_URL = 'postgresql+psycopg://' + DB_URL[len('postgresql://'):]
engine = create_engine(DB_URL, pool_pre_ping=True, connect_args={'check_same_thread': False} if DB_URL.startswith('sqlite:') else {})
Base = declarative_base()
class Registration(Base):
    __tablename__ = 'registrations'
    id = Column(Integer, primary_key=True)
    token = Column(String(80), unique=True, nullable=False)
    name = Column(String(90), nullable=False)
    account = Column(String(20), nullable=False)
    server = Column(String(100), nullable=False)
    lot = Column(String(8), nullable=False)
    status = Column(String(24), nullable=False, default='Pending Approval')
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
Base.metadata.create_all(engine)
app = FastAPI(title='BIG BULL COPY - Registration')

def safe(v): return html.escape(str(v), quote=True)
def page(title, body):
    return HTMLResponse(f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{safe(title)} | BIG BULL COPY</title><style>
    *{{box-sizing:border-box}}body{{font-family:Arial,sans-serif;background:#0b1220;color:#f1f5f9;margin:0;padding:28px 14px}}main{{max-width:800px;margin:auto}}.brand{{font-size:29px;font-weight:800;color:#f5c76e;letter-spacing:1px}}.card{{background:#172235;border:1px solid #334155;border-radius:16px;padding:24px;margin-top:22px}}h1{{font-size:24px}}p{{line-height:1.6;color:#cbd5e1}}label{{display:block;margin:14px 0 6px}}input,select{{width:100%;padding:13px;border-radius:8px;border:1px solid #64748b;background:#0f172a;color:white;font-size:16px}}button,.btn{{display:inline-block;margin-top:20px;padding:12px 20px;background:#eab85f;color:#111827;border:0;border-radius:8px;font-weight:700;cursor:pointer;text-decoration:none}}a{{color:#f5c76e}}.note{{font-size:13px;color:#bac5d5}}table{{width:100%;border-collapse:collapse}}td,th{{padding:10px;border-bottom:1px solid #334155;text-align:left;overflow-wrap:anywhere}}.actions{{display:flex;gap:6px;flex-wrap:wrap}}.actions button{{margin:0;padding:8px}}.danger{{background:#fda4af}}.scroll{{overflow-x:auto}}</style></head><body><main><div class="brand">🐂 BIG BULL COPY</div>{body}</main></body></html>''', headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'"})

def admin_auth(request):
    import base64
    user = os.getenv('ADMIN_USER','admin')
    password = os.getenv('ADMIN_PASSWORD','')
    if len(password) < 16:
        raise HTTPException(503, 'Set ADMIN_PASSWORD env variable (at least 16 characters)')
    header = request.headers.get('Authorization','')
    try:
        scheme, token = header.split(' ',1)
        raw = base64.b64decode(token,validate=True).decode()
        supplied_user, supplied_pass = raw.split(':',1)
        ok = scheme.lower() == 'basic' and hmac.compare_digest(supplied_user,user) and hmac.compare_digest(supplied_pass,password)
    except (ValueError, UnicodeError): ok=False
    if not ok:
        raise HTTPException(401,'Admin login required',headers={'WWW-Authenticate':'Basic realm="BIG BULL Admin"'})

def same_origin(request):
    origin=request.headers.get('origin','')
    if origin and origin.rstrip('/') != str(request.base_url).rstrip('/'):
        raise HTTPException(403,'Origin mismatch')

@app.get('/',response_class=HTMLResponse)
def index():
    return page('Client Registration','''<div class="card"><h1>Client Registration</h1><p>Submit your MT5 <b>demo</b> account information for review. <b>No password is required.</b></p><form method="post" action="/register"><label>Your name</label><input name="name" maxlength="90" required><label>MT5 Demo Account ID</label><input name="account" inputmode="numeric" pattern="[0-9]{4,15}" required maxlength="15"><label>Broker server</label><input name="server" maxlength="100" required><label>Fixed lot (preference only)</label><select name="lot"><option>0.01</option><option>0.02</option><option>0.05</option><option>0.10</option></select><button type="submit">Submit for Approval</button></form><p class="note">Registration and approval do not activate trading. Never share your MT5 password here. Trading carries risk.</p></div>''')

@app.post('/register')
def register(name:str=Form(...),account:str=Form(...),server:str=Form(...),lot:str=Form('0.01')):
    name=name.strip();server=server.strip();account=account.strip()
    if not (1<=len(name)<=90 and 1<=len(server)<=100 and account.isascii() and account.isdigit() and 4<=len(account)<=15 and lot in ['0.01','0.02','0.05','0.10']):
        raise HTTPException(422,'Invalid registration details')
    token=secrets.token_urlsafe(32)
    with Session(engine) as db:
        count=db.scalar(select(func.count()).select_from(Registration))
        if count>=25: raise HTTPException(409,'Registration capacity reached (25)')
        db.add(Registration(token=token,name=name,account=account,server=server,lot=lot))
        db.commit()
    return RedirectResponse('/status/'+quote(token),status_code=303)

@app.get('/status/{token}',response_class=HTMLResponse)
def status(token:str):
    with Session(engine) as db:
        registration=db.scalar(select(Registration).where(Registration.token==token))
        if not registration: raise HTTPException(404,'Invalid registration link')
        state=registration.status
    return page('Registration Status',f'<div class="card"><h1>Registration received</h1><p>Your registration status: <strong>{safe(state)}</strong></p><p>Save this private link to check your request later.</p><p class="note">Even if approved, actual MT5 copying is NOT active. A separately authorized and tested copier connection is required.</p><a class="btn" href="/">Home</a></div>')

@app.get('/admin',response_class=HTMLResponse)
def admin(request:Request):
    admin_auth(request)
    with Session(engine) as db:
        rows=db.scalars(select(Registration).order_by(Registration.id.desc())).all()
        cells=''.join(f'<tr><td>{r.id}</td><td>{safe(r.name)}</td><td>{safe(r.account)}</td><td>{safe(r.server)}</td><td>{safe(r.lot)}</td><td>{safe(r.status)}</td><td><div class="actions"><form method="post" action="/admin/{r.id}/approve"><button>Approve</button></form><form method="post" action="/admin/{r.id}/reject"><button class="danger">Reject</button></form></div></td></tr>' for r in rows)
    return page('Admin Approval',f'<div class="card"><h1>Admin Approval</h1><p>Registrations: {len(rows)} / 25. Approving is administrative only; it never starts trades.</p><div class="scroll"><table><tr><th>#</th><th>Name</th><th>MT5 ID</th><th>Server</th><th>Lot</th><th>Status</th><th>Actions</th></tr>{cells}</table></div><p class="note">Do not use real trading credentials. Admin authentication uses HTTPS Basic Auth; production requires additional hardening and abuse protection.</p></div>')

@app.post('/admin/{registration_id}/{action}')
def update(request:Request,registration_id:int,action:str):
    admin_auth(request);same_origin(request)
    if action not in ['approve','reject']: raise HTTPException(404)
    with Session(engine) as db:
        reg=db.get(Registration,registration_id)
        if not reg: raise HTTPException(404)
        reg.status='Approved — Connection Required' if action=='approve' else 'Rejected'
        db.commit()
    return RedirectResponse('/admin',status_code=303)

@app.get('/health')
def health(): return {'ok':True,'product':'BIG BULL COPY Registration','copy_trading_active':False}
