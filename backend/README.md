# Student Portal Backend (Flask + MongoDB)

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set environment variables:
   ```bash
   export MONGO_URI="mongodb://localhost:27017/student_portal"
   export JWT_SECRET="super-secret-key"
   export JWT_EXPIRY_HOURS="24"
   ```
4. Run server:
   ```bash
   python app.py
   ```

The API runs on `http://localhost:5000`.

## API Endpoints

- `GET /api/health` - API health check.
- `POST /api/register` - Register a student and return JWT token.
- `POST /api/login` - Student login and return JWT token.
- `GET /api/jobs` - List jobs.
- `POST /api/jobs` - Create a job.
- `POST /api/jobs/<job_id>/apply` - Apply to a job.
- `GET /api/students/<student_id>/profile` - Get student profile (projects, marks, skills, etc).

## Example Payloads

### Register

```json
{
  "name": "Alice",
  "email": "alice@example.com",
  "password": "secure-pass",
  "skills": ["Python", "Flask"],
  "projects": [
    {
      "title": "Placement Portal",
      "description": "Built an internal job portal"
    }
  ],
  "marks": {
    "10th": 91,
    "12th": 88,
    "cgpa": 8.7
  }
}
```

### Register/Login Response (sample)

```json
{
  "message": "Student registered successfully",
  "student_id": "<student_object_id>",
  "role": "student",
  "token": "<jwt_token>"
}
```

### Apply to Job

```json
{
  "student_id": "<student_object_id>"
}
```
