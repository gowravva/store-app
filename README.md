# The Store — Dockerized + CI/CD

A simple, self-contained shop: **frontend + backend + database, all in one app.**
It owns its own products, stock and orders — nothing else needs to run.

```
applicaion1/
├── docker-compose.yml           # runs the whole app (backend + frontend)
├── .env.example                 # copy to .env and fill in
├── .github/workflows/deploy.yml # CI/CD: build + deploy on every push to main
└── store-app/
    ├── backend/                 # FastAPI, port 8001
    │   ├── main.py                  the API
    │   ├── database.py              Product + Order tables
    │   ├── store.db                 the database (SQLite = one file)
    │   └── Dockerfile
    └── frontend/                # React + Vite -> nginx static
        ├── Dockerfile
        └── nginx.conf
```

## The three parts

| Part | What it is | Where |
|---|---|---|
| **Frontend** | The shop page users see | `frontend/` (React) |
| **Backend** | The API / logic | `backend/main.py` (FastAPI) |
| **Database** | Products + orders | `backend/store.db` (SQLite) |

## API endpoints
- `GET  /catalog` — list products for sale
- `POST /checkout` — sell a product (reduces stock, records the order)
- `GET  /orders` — every sale, newest first
- `POST /products` — add a new product
- `POST /products/{id}/restock` — add more stock

The backend seeds a few demo products on first run, so the shop isn't empty.

## Run it locally — the simple way (no Docker)

```bash
# backend
cd store-app/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8001      # http://localhost:8001/docs

# frontend (in a second terminal)
cd store-app/frontend
npm install
npm run dev                                # http://localhost:5173
```

## Run it with Docker

```bash
cp .env.example .env
docker compose up -d --build
```
- Shopfront: http://localhost:8080
- Backend API docs: http://localhost:8001/docs

## CI/CD — auto-deploy on every push

### 1. Push to GitHub
```bash
git add .
git commit -m "Simple self-contained Store app + Docker + CI/CD"
git branch -M main
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

### 2. Add GitHub Secrets
Repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Value |
|---|---|
| `SERVER_HOST` | Server public IP (e.g. `141.148.x.x`) |
| `SERVER_USER` | SSH user (OCI = `opc`, Ubuntu = `ubuntu`) |
| `SSH_PRIVATE_KEY` | **Full** contents of your private key (incl. `-----BEGIN...`) |

### 3. Prepare the server (one time)
```bash
# install Docker + compose plugin, then:
sudo systemctl enable --now docker
sudo usermod -aG docker $USER   # log out/in after this
```
Open ports **8080** (shopfront) and **8001** (API) in your cloud firewall.

### 4. Push to deploy
Every `git push` to `main` now:
1. Builds both Docker images (fails fast if code is broken)
2. Copies the project to the server over SSH
3. Runs `docker compose up -d --build`

Watch it live in the repo's **Actions** tab, then open `http://<SERVER_HOST>:8080`.
