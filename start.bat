@echo off
echo ============================================================
echo   Attention-Aware Study Assistant — Launcher
echo ============================================================
echo.

REM Activate venv
call venv\Scripts\activate

echo Starting FastAPI backend on port 8000...
start "Backend" cmd /k "venv\Scripts\python run_server.py"

echo Waiting for backend to start...
timeout /t 3 /nobreak > nul

echo Starting Streamlit frontend on port 8501...
start "Frontend" cmd /k "venv\Scripts\streamlit run frontend\app.py --server.headless true --server.port 8501"

echo.
echo ============================================================
echo   Backend:  http://localhost:8000/docs
echo   Frontend: http://localhost:8501
echo ============================================================
echo.
echo Press any key to stop all services...
pause > nul

taskkill /FI "WINDOWTITLE eq Backend" /F > nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend" /F > nul 2>&1
echo Services stopped.
