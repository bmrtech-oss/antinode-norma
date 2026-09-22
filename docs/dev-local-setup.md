```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
pip install -r requirements-dev.txt
Copy-Item .env.example .env
cd ui
npm install
npm run build
cd ..
uvicorn antinode_norma.server.api:app --host 0.0.0.0 --port 8000
curl http://localhost:8000/health
cd ui
npm run dev
```
