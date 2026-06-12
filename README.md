# Life K-Line Engine

Astrological Life K-Line Scoring Engine for calculating astrological dignities, aspects, houses, and receptions.

## Features

- **Dignities Calculation**: Essential and accidental dignities
- **Aspect Analysis**: Major and minor aspects with orbs
- **House System**: Multiple house systems support
- **Reception Analysis**: Mutual reception and dispositors
- **Scoring System**: Comprehensive scoring for planetary positions

## Installation

```bash
pip install life-kline-engine
```

## Development

Backend:

```bash
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Environment

Frontend defaults to `VITE_API_BASE_URL=/api` and uses the Vite dev proxy in development.
You can copy `frontend/.env.example` and override these values as needed:

```bash
VITE_API_BASE_URL=/api
VITE_DEV_PROXY_TARGET=http://127.0.0.1:8000
```

Backend reads these optional environment variables:

```bash
LIFE_KLINE_HOST=0.0.0.0
LIFE_KLINE_PORT=8000
LIFE_KLINE_CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
LIFE_KLINE_GEOCODE_TIMEOUT=4
LIFE_KLINE_AMAP_KEY=your_amap_web_service_key
```

You can put these values in `backend/.env` or `backend/.env.local`. A ready-to-edit template is provided at `backend/.env.example`.

When `LIFE_KLINE_AMAP_KEY` is configured, `/api/geocode` will try AMap first and then fall back to the public providers. AMap returns GCJ-02 coordinates, so the backend converts them back to WGS84 before returning `lat` and `lon`.
