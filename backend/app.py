import os
from datetime import datetime, timedelta, timezone

import jwt
from bson import ObjectId
from flask import Flask, jsonify, request
from pymongo import MongoClient
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/student_portal")
JWT_SECRET = os.getenv("JWT_SECRET", "change-this-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))

client = MongoClient(MONGO_URI)
db = client.get_database("student_portal")

students_collection = db["students"]
jobs_collection = db["jobs"]
applications_collection = db["applications"]


def serialize_document(document: dict) -> dict:
    serialized = {}
    for key, value in document.items():
        if isinstance(value, ObjectId):
            serialized[key] = str(value)
        elif isinstance(value, list):
            serialized[key] = [str(item) if isinstance(item, ObjectId) else item for item in value]
        else:
            serialized[key] = value
    return serialized


def parse_object_id(value: str, field_name: str):
    if not value:
        return None, jsonify({"error": f"{field_name} is required"}), 400
    try:
        return ObjectId(value), None, None
    except Exception:
        return None, jsonify({"error": f"Invalid {field_name}"}), 400


def create_jwt_token(student: dict) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(student["_id"]),
        "email": student["email"],
        "name": student["name"],
        "role": student.get("role", "student"),
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@app.get("/api/health")
def health_check():
    return jsonify({"status": "ok"})


@app.post("/api/register")
def register_student():
    payload = request.get_json(silent=True) or {}

    name = payload.get("name")
    email = payload.get("email")
    password = payload.get("password")

    if not name or not email or not password:
        return jsonify({"error": "name, email and password are required"}), 400

    if students_collection.find_one({"email": email.lower()}):
        return jsonify({"error": "Student with this email already exists"}), 409

    student_document = {
        "name": name,
        "email": email.lower(),
        "password_hash": generate_password_hash(password),
        "role": "student",
        "skills": payload.get("skills", []),
        "projects": payload.get("projects", []),
        "marks": payload.get("marks", {}),
        "created_at": datetime.utcnow(),
    }

    insert_result = students_collection.insert_one(student_document)
    student_document["_id"] = insert_result.inserted_id
    token = create_jwt_token(student_document)

    return (
        jsonify(
            {
                "message": "Student registered successfully",
                "student_id": str(insert_result.inserted_id),
                "role": student_document["role"],
                "token": token,
            }
        ),
        201,
    )


@app.post("/api/login")
def login_student():
    payload = request.get_json(silent=True) or {}

    email = payload.get("email")
    password = payload.get("password")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    student = students_collection.find_one({"email": email.lower()})

    if not student or not check_password_hash(student["password_hash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_jwt_token(student)

    return jsonify(
        {
            "message": "Login successful",
            "student_id": str(student["_id"]),
            "name": student["name"],
            "role": student.get("role", "student"),
            "token": token,
        }
    )


@app.get("/api/jobs")
def list_jobs():
    jobs = [serialize_document(job) for job in jobs_collection.find()]
    return jsonify(jobs)


@app.post("/api/jobs")
def create_job():
    payload = request.get_json(silent=True) or {}

    title = payload.get("title")
    company = payload.get("company")
    description = payload.get("description")

    if not title or not company or not description:
        return jsonify({"error": "title, company and description are required"}), 400

    job_document = {
        "title": title,
        "company": company,
        "description": description,
        "location": payload.get("location", ""),
        "required_skills": payload.get("required_skills", []),
        "created_at": datetime.utcnow(),
    }

    insert_result = jobs_collection.insert_one(job_document)

    return (
        jsonify({"message": "Job created", "job_id": str(insert_result.inserted_id)}),
        201,
    )


@app.post("/api/jobs/<job_id>/apply")
def apply_for_job(job_id):
    payload = request.get_json(silent=True) or {}

    student_id_raw = payload.get("student_id")
    student_object_id, error_response, status_code = parse_object_id(student_id_raw, "student_id")
    if error_response:
        return error_response, status_code

    job_object_id, error_response, status_code = parse_object_id(job_id, "job_id")
    if error_response:
        return error_response, status_code

    student = students_collection.find_one({"_id": student_object_id})
    if not student:
        return jsonify({"error": "Student not found"}), 404

    job = jobs_collection.find_one({"_id": job_object_id})
    if not job:
        return jsonify({"error": "Job not found"}), 404

    if applications_collection.find_one({"student_id": student_object_id, "job_id": job_object_id}):
        return jsonify({"error": "Student has already applied for this job"}), 409

    applications_collection.insert_one(
        {
            "student_id": student_object_id,
            "job_id": job_object_id,
            "status": "applied",
            "applied_at": datetime.utcnow(),
        }
    )

    return jsonify({"message": "Application submitted successfully"}), 201


@app.get("/api/students/<student_id>/profile")
def get_student_profile(student_id):
    student_object_id, error_response, status_code = parse_object_id(student_id, "student_id")
    if error_response:
        return error_response, status_code

    student = students_collection.find_one({"_id": student_object_id})
    if not student:
        return jsonify({"error": "Student not found"}), 404

    profile = {
        "student_id": str(student["_id"]),
        "name": student.get("name"),
        "email": student.get("email"),
        "skills": student.get("skills", []),
        "projects": student.get("projects", []),
        "marks": student.get("marks", {}),
    }

    return jsonify(profile)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )
