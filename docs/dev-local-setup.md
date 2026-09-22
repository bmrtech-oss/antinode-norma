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
bash ./scripts/backend.sh start
curl http://localhost:8000/health
bash ./scripts/frontend.sh start
bash ./scripts/frontend.sh status
bash ./scripts/frontend.sh stop
bash ./scripts/backend.sh stop
```
