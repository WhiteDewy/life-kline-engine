
@echo off
echo Starting Life K-Line Backend Server...
echo Ensure you have installed dependencies: pip install -r backend/requirements.txt
echo.

set PYTHONPATH=%PYTHONPATH%;%CD%\src

if "%LIFE_KLINE_HOST%"=="" set LIFE_KLINE_HOST=0.0.0.0
if "%LIFE_KLINE_PORT%"=="" set LIFE_KLINE_PORT=8000
if "%LIFE_KLINE_CORS_ORIGINS%"=="" set LIFE_KLINE_CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173

echo Using host %LIFE_KLINE_HOST% and port %LIFE_KLINE_PORT%
if exist backend\.env (
    echo backend\.env detected. backend.main will load it automatically.
) else (
    echo backend\.env not found. Copy backend\.env.example to backend\.env and fill LIFE_KLINE_AMAP_KEY if needed.
)
if "%LIFE_KLINE_AMAP_KEY%"=="" (
    echo LIFE_KLINE_AMAP_KEY is not set in the current shell. backend\.env or backend\.env.local may still provide it.
) else (
    echo AMap geocoding enabled.
)

python -m uvicorn backend.main:app --reload --host %LIFE_KLINE_HOST% --port %LIFE_KLINE_PORT%
