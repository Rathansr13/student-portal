# Proxy Server (Flask)

This proxy server accepts client requests and forwards `/api/*` calls to the backend service.
It also performs JWT role-based authorization before forwarding protected routes.

## Configuration

Set environment variables:

```bash
export BACKEND_BASE_URL="http://localhost:5000"
export JWT_SECRET="super-secret-key"
```

> `JWT_SECRET` in proxy must match backend `JWT_SECRET`.

## Run

```bash
pip install -r requirements.txt
python app.py
```

The proxy starts on `http://localhost:5001`.

## Routes and Role Rules

Public routes (no JWT required):
- `GET /api/health`
- `POST /api/register`
- `POST /api/login`
- `GET /api/jobs`

Protected routes:
- `POST /api/jobs` -> `admin`
- `POST /api/jobs/<job_id>/apply` -> `student` or `admin`
- `GET /api/students/<student_id>/profile` -> `student` or `admin`
- any other `/api/*` route defaults to `admin`

Send JWT in request header:

```bash
Authorization: Bearer <token>
```
