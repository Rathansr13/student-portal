# Proxy Server (Flask)

This proxy server accepts client requests and forwards `/api/*` calls to the backend service.

## Configuration

Set the backend URL (defaults to `http://localhost:5000`):

```bash
export BACKEND_BASE_URL="http://localhost:5000"
```

## Run

```bash
pip install -r requirements.txt
python app.py
```

The proxy starts on `http://localhost:5001`.

## Routes

- `GET /health` - proxy health check.
- `/api/*` - forwards all supported HTTP methods to backend `/api/*`.
