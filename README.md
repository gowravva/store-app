# The Store — React + FastAPI, with CI/CD

A simple, self-contained shop: **React frontend + FastAPI backend + SQLite database.**
It owns its own products, stock and orders — nothing else needs to run.
Deployed by pushing code straight to an AWS EC2 server (no Docker).

```
applicaion1/
├── .github/workflows/deploy.yml  # CI/CD: build + deploy on every push to main
├── deploy/
│   ├── store-backend.service     # systemd unit (keeps the backend running)
│   └── nginx-store.conf          # nginx config (serves the frontend)
└── store-app/
    ├── backend/                  # FastAPI, port 8001
    │   ├── main.py                   the API
    │   ├── database.py               Product + Order tables
    │   └── store.db                  the database (SQLite = one file)
    └── frontend/                 # React + Vite
        └── src/App.jsx
```

## The three parts

| Part | Technology | Where |
|---|---|---|
| **Frontend** | React + Vite | `store-app/frontend/` |
| **Backend** | FastAPI (Python) | `store-app/backend/main.py` |
| **Database** | SQLite | `store-app/backend/store.db` |

## Run it locally

Two terminals:

```bash
# Terminal 1 — backend
cd store-app/backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8001     # http://localhost:8001/docs

# Terminal 2 — frontend
cd store-app/frontend
npm install
npm run dev                                          # http://localhost:5173
```

Open http://localhost:5173.

## Deploy to a server — CI/CD on every push

### How it works
On every push to `main`, GitHub Actions:
1. **build** — installs the backend, import-checks it, and builds the frontend (fails fast if broken)
2. **deploy** — copies the code to your EC2 server over SSH, then:
   - backend: creates a Python venv, installs deps, runs it via a **systemd** service
   - frontend: `npm run build`, copies the static files into **nginx**

### 1. Prepare the EC2 server (one time)
SSH in (`ssh -i key.pem ec2-user@<IP>`) and install what's needed:
```bash
sudo dnf install -y python3 python3-pip nodejs npm nginx
sudo systemctl enable --now nginx
```
Open ports **80** (website) and **8001** (API) in the instance's **Security Group**.

### 2. Add GitHub Secrets
Repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Value |
|---|---|
| `SERVER_HOST` | EC2 **public IPv4** (e.g. `13.233.x.x`) |
| `SERVER_USER` | `ec2-user` |
| `SSH_PRIVATE_KEY` | **Full** contents of your `.pem` key (incl. `-----BEGIN...`) |

### 3. Deploy
Push to `main` (or use **Run workflow** in the Actions tab). Then open:
- Website: `http://<SERVER_HOST>/`
- API docs: `http://<SERVER_HOST>:8001/docs`

> The frontend is served on port **80**, so the site is just `http://<SERVER_HOST>`.
> Note: an EC2 public IP changes on stop/start — attach an **Elastic IP** to keep it fixed.
