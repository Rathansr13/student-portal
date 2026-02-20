import os

import jwt
import requests
from flask import Flask, Response, jsonify, request

app = Flask(__name__)

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:5000")
JWT_SECRET = os.getenv("JWT_SECRET", "change-this-secret")
JWT_ALGORITHM = "HS256"

EXCLUDED_HEADERS = {
    "content-encoding",
    "content-length",
    "transfer-encoding",
    "connection",
}

PUBLIC_ROUTES = {
    ("GET", "/api/health"),
    ("POST", "/api/register"),
    ("POST", "/api/login"),
    ("GET", "/api/jobs"),
}


ROLE_RULES = [
    {"method": "POST", "path_prefix": "/api/jobs/", "path_suffix": "/apply", "roles": {"student", "admin"}},
    {"method": "GET", "path_prefix": "/api/students/", "path_suffix": "/profile", "roles": {"student", "admin"}},
    {"method": "POST", "path_prefix": "/api/jobs", "path_suffix": "", "exact": "/api/jobs", "roles": {"admin"}},
]


def build_target_url(path: str) -> str:
    return f"{BACKEND_BASE_URL.rstrip('/')}/{path.lstrip('/')}"


def parse_bearer_token(auth_header: str):
    if not auth_header:
        return None
    prefix = "Bearer "
    if not auth_header.startswith(prefix):
        return None
    return auth_header[len(prefix) :].strip()


def decode_jwt_token(token: str):
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def get_required_roles(method: str, path: str):
    for route_method, route_path in PUBLIC_ROUTES:
        if method == route_method and path == route_path:
            return set()

    for rule in ROLE_RULES:
        if method != rule["method"]:
            continue

        if "exact" in rule and path == rule["exact"]:
            return rule["roles"]

        if path.startswith(rule["path_prefix"]) and path.endswith(rule["path_suffix"]):
            return rule["roles"]

    return {"admin"}


def authorize_request():
    required_roles = get_required_roles(request.method, request.path)
    if not required_roles:
        return None

    token = parse_bearer_token(request.headers.get("Authorization", ""))
    if not token:
        return jsonify({"error": "Missing or invalid Authorization header"}), 401

    try:
        payload = decode_jwt_token(token)
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    role = payload.get("role")
    if role not in required_roles:
        return (
            jsonify({"error": "Forbidden for role", "required_roles": sorted(required_roles)}),
            403,
        )

    return None


@app.get("/health")
def health_check():
    return jsonify({"status": "ok", "proxying_to": BACKEND_BASE_URL})


@app.route("/api/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@app.route("/api", defaults={"path": ""}, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
def proxy_api(path):
    auth_error = authorize_request()
    if auth_error:
        return auth_error

    target_url = build_target_url(f"api/{path}")

    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() != "host"
    }

    try:
        upstream_response = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            params=request.args,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=20,
        )
    except requests.RequestException as error:
        return jsonify({"error": "Unable to reach backend service", "details": str(error)}), 502

    response_headers = [
        (name, value)
        for name, value in upstream_response.raw.headers.items()
        if name.lower() not in EXCLUDED_HEADERS
    ]

    return Response(upstream_response.content, upstream_response.status_code, response_headers)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5001")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )
