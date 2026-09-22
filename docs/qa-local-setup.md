```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
pip install -r requirements-dev.txt
Copy-Item .env.docker.example .env
cd ui
npm install
npm run build
npm run test
npm run test:e2e
cd ..
uvicorn antinode_norma.server.api:app --host 0.0.0.0 --port 8000
curl http://localhost:8000/health
curl http://localhost:8000/api/dashboard
```
