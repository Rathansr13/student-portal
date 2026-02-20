import os

import requests
from flask import Flask, Response, jsonify, request

app = Flask(__name__)

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "https://student-portal-y3nh.onrender.com/")


EXCLUDED_HEADERS = {
    "content-encoding",
    "content-length",
    "transfer-encoding",
    "connection",
}


def build_target_url(path: str) -> str:
    return f"{BACKEND_BASE_URL.rstrip('/')}/{path.lstrip('/')}"


@app.get("/health")
def health_check():
    return jsonify({"status": "ok", "proxying_to": BACKEND_BASE_URL})


@app.route("/api/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@app.route("/api", defaults={"path": ""}, methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
def proxy_api(path):
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
    app.run(host="0.0.0.0", port=5001, debug=True)
