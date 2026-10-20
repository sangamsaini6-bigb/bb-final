# BIG BULL COPY — Registration / Approval Prototype

This repo is a **registration-only** FastAPI website. Client page: `/`; admin page: `/admin`; client status page link appears after signup. No broker connection, no passwords, no copier, no trade execution. Approving a user only changes their *approval status*.

## Deploy on Render

1. Upload `app.py`, `requirements.txt`, `.gitignore`, and `README.md` as **individual files to the repository root**. Do NOT upload the ZIP itself.
2. Render → New → Web Service → connect your GitHub repo.
3. Runtime: Python. Build command: `pip install -r requirements.txt`.
4. Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`.
5. Add environment variables: `ADMIN_USER` (example `admin`) and **`ADMIN_PASSWORD`** (a UNIQUE random password at least 16 characters, Render environment only; NEVER place in GitHub).
6. **Data persistence:** connect a Render Postgres instance and set `DATABASE_URL` to its internal connection URL. Without this, fallback SQLite storage on ephemeral web-service disk can be LOST when restarted/redeployed, so do not rely on it for real signups. Free database options/limits may change.
7. Deploy. Use your assigned `https://...onrender.com/` URL for client registrations and `/admin` for admin approvals.

## Security and scope

- The repository can be public, since no passwords or secrets are in its files. Never commit `.env`, credentials, MT5 passwords, account exports, or private client data.
- HTTPS must be used for the admin page. Authentication is HTTP Basic; use a strong password.
- This is a **test/demo MVP**: it does not have client accounts/login, abuse/rate limits, CSRF tokens, email validation, privacy policy, account-ownership verification, or production security audit. Before onboarding live clients add those, and assess trading/broker/legal permissions.
- Limit currently counts all registrations toward 25, including rejected ones.
- Client status links act as private bearer links: clients should not forward them.
- Test with demo IDs only. Connection to MT5 Windows workers is a separate phase.

Local: `pip install -r requirements.txt` then set ADMIN_PASSWORD (16+ chars) and run `uvicorn app:app --reload`.
