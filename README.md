<div align="center">

<!-- Animated Header Banner -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:6366f1,50:8b5cf6,100:06b6d4&height=300&section=header&text=LookIn%20AI&fontSize=80&fontColor=ffffff&animation=fadeIn&fontAlignY=35&desc=AI-Powered%20Face%20Recognition%20Attendance%20System&descSize=22&descAlignY=55&descAlign=50" width="100%" />

<!-- Animated Badges -->
<p>
  <a href="#"><img src="https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge&logo=django&logoColor=white&labelColor=092E20" alt="Django" /></a>
  <a href="#"><img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=3776AB" alt="Python" /></a>
  <a href="#"><img src="https://img.shields.io/badge/InsightFace-Buffalo_L-FF6F61?style=for-the-badge&logo=opencv&logoColor=white&labelColor=FF6F61" alt="InsightFace" /></a>
  <a href="#"><img src="https://img.shields.io/badge/OpenCV-4.x-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white&labelColor=5C3EE8" alt="OpenCV" /></a>
  <a href="#"><img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white&labelColor=2496ED" alt="Docker" /></a>
  <a href="#"><img src="https://img.shields.io/badge/PostgreSQL-NeonDB-4169E1?style=for-the-badge&logo=postgresql&logoColor=white&labelColor=4169E1" alt="PostgreSQL" /></a>
  <a href="#"><img src="https://img.shields.io/badge/Multi--Tenant-SaaS-10b981?style=for-the-badge&logo=cloudflare&logoColor=white&labelColor=10b981" alt="Multi-Tenant" /></a>
  <a href="#"><img src="https://img.shields.io/badge/B2B_REST_API-v1-f59e0b?style=for-the-badge&logo=fastapi&logoColor=white&labelColor=f59e0b" alt="B2B API" /></a>
</p>

<!-- Animated Typing -->
<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&weight=600&size=24&duration=3000&pause=1000&color=8B5CF6&center=true&vCenter=true&multiline=true&repeat=true&width=750&height=160&lines=🎯+Real-Time+Face+Recognition+Attendance;📸+Group+Photo+%2B+Video+%2B+Live+Webcam;🤖+Powered+by+InsightFace+Buffalo_L+Model;🏢+Multi-Tenant+SaaS+%7C+B2B+REST+API" alt="Typing SVG" /></a>

<br />

<!-- Stats -->
<a href="https://lookinai.gdgdau.cloud"><img src="https://img.shields.io/badge/🌐_LIVE_DEMO-lookinai.gdgdau.cloud-22c55e?style=for-the-badge&labelColor=16a34a" alt="Live Demo" /></a>

<br /><br />

<!-- Stats -->
<img src="https://img.shields.io/badge/Accuracy-95%25+-brightgreen?style=flat-square" />
<img src="https://img.shields.io/badge/Processing-<3s_per_photo-blue?style=flat-square" />
<img src="https://img.shields.io/badge/Models-512D_Embeddings-purple?style=flat-square" />
<img src="https://img.shields.io/badge/Tenants-Multi--College-orange?style=flat-square" />
<img src="https://img.shields.io/badge/Liveness-3--Frame_Check-red?style=flat-square" />

</div>

---

## 📋 Table of Contents

<details>
<summary>Click to expand</summary>

- [✨ Overview](#-overview)
- [🚀 Key Features](#-key-features)
- [🆕 What's New](#-whats-new)
- [🏗️ System Architecture](#️-system-architecture)
- [🧠 AI Pipeline](#-ai-pipeline)
- [🏢 Multi-Tenant Architecture](#-multi-tenant-architecture)
- [🔌 B2B REST API](#-b2b-rest-api)
- [🔑 API Key Management](#-api-key-management)
- [📁 Project Structure](#-project-structure)
- [📊 Database Models](#-database-models)
- [🔗 API Endpoints](#-api-endpoints)
- [⚙️ Tech Stack](#️-tech-stack)
- [🛠️ Installation & Setup](#️-installation--setup)
- [🐳 Docker Deployment](#-docker-deployment)
- [🔐 Environment Variables](#-environment-variables)
- [🧪 Testing](#-testing)
- [📱 User Roles & Workflows](#-user-roles--workflows)
- [📈 Performance Optimizations](#-performance-optimizations)
- [🤝 Contributing](#-contributing)

</details>

---

## ✨ Overview

<div align="center">

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   LookIn AI is an intelligent attendance management system      │
│   that uses state-of-the-art face recognition technology        │
│   to automate the attendance marking process in educational     │
│   institutions.                                                 │
│                                                                 │
│   Built with Django + InsightFace + OpenCV, it supports         │
│   group photo analysis, video processing, and real-time         │
│   live webcam scanning for hands-free attendance marking.       │
│                                                                 │
│   Now featuring Multi-Tenant SaaS architecture for multiple     │
│   colleges and a B2B REST API for Flutter/mobile integration.   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

</div>

**LookIn AI** eliminates the tedious manual roll-call process by leveraging deep learning-based face recognition. Teachers can simply upload a **group photo**, record a **video** of the classroom, or start a **live webcam session** — and the system automatically identifies students, marks attendance, sends email notifications to absentees, and generates downloadable Excel reports.

Now with **Multi-Tenant SaaS** support, each college gets its own isolated data environment — and the new **B2B REST API** lets mobile/Flutter clients plug directly into the face recognition engine with full liveness detection.

> 🌐 **Try it live:** [lookinai.gdgdau.cloud](https://lookinai.gdgdau.cloud)

---

## 🚀 Key Features

<table>
<tr>
<td width="50%">

### 📸 Group Photo Attendance
- Upload class group photos
- Detect multiple faces using tiling + NMS
- Match against enrolled students only
- Automatic present/absent marking
- Supports large group photos (2000px+ via tiling)

### 🎥 Video-Based Attendance
- Upload classroom video recordings
- Smart sampling — processes every 50th frame
- Multi-frame confirmation (2+ frames required)
- Early exit when all students are confirmed
- Real-time progress tracking during processing

### 📹 Live Webcam Scanning
- Real-time face detection via webcam
- Admin creates live attendance sessions
- Students scan their face to mark present
- Anti-spoofing liveness detection built-in
- Session auto-transfers to permanent attendance log

### 🏢 Multi-Tenant SaaS
- Strict data isolation per college/institution
- Super Admin oversees all tenants
- Staff Admins see only their college's data
- `created_by` relationship enforced across all models
- Fully scalable for multiple institutions

</td>
<td width="50%">

### 🔌 B2B REST API
- `/api/v1/get-face-encoding/` endpoint for mobile clients
- Base64 image input — JSON embedding output
- 3-frame liveness detection enforced on every request
- Returns 512-D float32 embedding for matched face
- Designed for Flutter / Android / iOS integration

### 🔑 API Key Management
- Admins generate & manage API keys from dashboard
- Secure `secrets.token_hex(32)` key generation
- Bearer token authentication for all B2B requests
- Toggle key active/inactive status on the fly
- Full audit trail per API client

### 📧 Smart Email Notifications
- Automatic absent alert emails
- Attendance percentage included in every email
- Low attendance warnings (< 75% threshold)
- Batched email sending (10 per batch with delay)
- Division-aware filtering for core subjects

### 📊 Reports & Analytics
- Student-wise attendance dashboard
- Subject-wise attendance breakdown
- Cumulative attendance trend charts (Chart.js)
- Downloadable Excel (.xlsx) reports
- Date range and subject filters

### 🔐 Authentication & Security
- **Email-based login** (replaced username login)
- Email OTP verification on registration
- Strong password enforcement (8+ chars, uppercase, lowercase, digit, special)
- Google OAuth 2.0 social login
- CSRF protection on all form endpoints
- Admin-only access control with session guard
- Automated superuser provisioning in Docker

</td>
</tr>
</table>

---

## 🆕 What's New

> Latest major release — highlights of everything added on top of v1.

<div align="center">

| # | Feature | Category | Status |
|---|---------|----------|--------|
| 🏢 | **Multi-Tenant SaaS Architecture** — data isolation per college | Architecture | ✅ Shipped |
| 🔌 | **B2B REST API** — `/api/v1/get-face-encoding/` for Flutter/mobile | API | ✅ Shipped |
| 🧬 | **3-Frame Liveness Detection** — anti-spoofing on B2B API | AI / Security | ✅ Shipped |
| 🔑 | **API Key Management** — generate & manage Bearer tokens | Security | ✅ Shipped |
| 📧 | **Email Authentication Backend** — login via email (not username) | Auth | ✅ Shipped |
| 🐳 | **Automated Docker Superuser Provisioning** — zero-touch deployment | DevOps | ✅ Shipped |

</div>

---

## 🏗️ System Architecture

```mermaid
graph TB
    subgraph Client["🌐 Client Layer"]
        A[👨‍🏫 Admin Panel] --> |Upload Photo/Video| B
        C[📹 Live Scan Page] --> |Webcam Frame| B
        E[👨‍🎓 Student Portal] --> |View Attendance| B
        M[📱 Mobile / Flutter App] --> |Bearer Token + Base64| B
    end

    subgraph Server["⚙️ Django Backend"]
        B[URL Router] --> F[Views Layer]
        F --> G[Encoding Service]
        F --> H[Session Buffer]
        F --> I[Email Service]
        F --> T[Tenant Filter Middleware]
        F --> K2[API Key Auth Layer]
    end

    subgraph AI["🧠 AI Engine"]
        G --> J[InsightFace buffalo_l]
        J --> K[Face Detection]
        J --> L[512-D Embedding]
        L --> M2[Cosine Similarity Matching]
        G --> LV[3-Frame Liveness Check]
    end

    subgraph Tenant["🏢 Multi-Tenant Layer"]
        T --> SA[Super Admin — All Colleges]
        T --> CA[Staff Admin — Own College Only]
    end

    subgraph Storage["💾 Data Layer"]
        H --> N[(PostgreSQL / SQLite)]
        F --> O[Cloudinary CDN]
        G --> P[In-Memory Cache]
        K2 --> AK[(APIKey Table)]
    end

    style Client fill:#f0f4ff,stroke:#6366f1
    style Server fill:#fef3f2,stroke:#ef4444
    style AI fill:#ecfdf5,stroke:#10b981
    style Tenant fill:#fdf4ff,stroke:#a855f7
    style Storage fill:#fffbeb,stroke:#f59e0b
```

---

## 🧠 AI Pipeline

### Face Recognition Engine

The system uses **InsightFace's Buffalo_L** model — a production-grade face analysis framework that provides:

| Component | Details |
|-----------|---------|
| **Detection Model** | RetinaFace with MobileNet backbone |
| **Recognition Model** | ArcFace with ResNet-100 backbone |
| **Embedding Size** | 512-dimensional float32 vectors |
| **Detection Size** | 320×320 pixels (optimized for speed) |
| **Matching Method** | Cosine similarity |
| **Match Threshold** | 0.30 – 0.45 (multi-pass strategy) |
| **Runtime** | ONNX Runtime (CPU / CUDA) |

### Processing Pipeline

```
┌──────────┐    ┌──────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────┐
│  Input   │───▶│ Preproc  │───▶│  Detection   │───▶│  Embedding  │───▶│ Matching │
│ Photo /  │    │ CLAHE +  │    │ InsightFace  │    │  512-D Vec  │    │ Cosine   │
│ Video /  │    │ Unsharp  │    │  RetinaFace  │    │  ArcFace    │    │ Sim > θ  │
│ Base64   │    └──────────┘    └──────────────┘    └─────────────┘    └──────────┘
└──────────┘
      │
      ▼ (B2B API only)
┌──────────────┐
│  3-Frame     │
│  Liveness    │
│  Detection   │
└──────────────┘
```

### Multi-Pass Matching Strategy

The system uses a **3-pass matching algorithm** for group photos to maximize recognition accuracy:

| Pass | Threshold | Purpose |
|------|-----------|---------|
| **Pass 1** | `≥ 0.32` | High-confidence matches |
| **Pass 2** | `≥ 0.22` | Retry unmatched faces with relaxed threshold |
| **Pass 3** | `≥ 0.18` | Fallback with unique-best-match constraint |

### Image Preprocessing

- **CLAHE** (Contrast Limited Adaptive Histogram Equalization) on L-channel in LAB color space
- **Unsharp Mask** sharpening for out-of-focus photos
- **Tiling** for images > 2000px with 25% overlap + NMS deduplication
- **Test-Time Augmentation (TTA)**: Original + Horizontal Flip + Brightness boost → embeddings averaged
- **Auto-upscale** small images (< 200px) using cubic interpolation

### Video Processing

- **Smart Sampling**: Every 50th frame is processed (not every frame)
- **Frame Preprocessing**: Resize to max 640px before AI processing
- **Multi-Frame Confirmation**: Student must be detected in 2+ frames to count as present
- **Early Exit**: Stops processing once all enrolled students are confirmed
- **ThreadPool Parallel Processing**: Multiple files processed concurrently via `ThreadPoolExecutor(max_workers=4)`

### Anti-Spoofing: Liveness Detection

```python
# Standard webcam liveness (live scan page):
# Pixel-diff on 64×64 downsampled grayscale frames
# Requires 3-5 frames captured ~300ms apart
# Variance threshold: 1.8 (prevents photo/screen attacks)
# Processing time: < 0.1s total

# B2B API liveness (strict):
# Requires EXACTLY 3 frames in the JSON payload
# All 3 frames analysed for motion variance
# liveness_passed: true/false returned in response
# Embedding only returned if liveness_passed == true
```

---

## 🏢 Multi-Tenant Architecture

LookIn AI now operates as a **true multi-tenant SaaS platform**, allowing multiple colleges and institutions to share a single deployment while keeping all data completely isolated.

```mermaid
graph TD
    SA[🛡️ Super Admin] --> CA1[🏫 College A Admin]
    SA[🛡️ Super Admin] --> CA2[🏫 College B Admin]
    SA[🛡️ Super Admin] --> CA3[🏫 College C Admin]

    CA1 --> S1[Students A]
    CA1 --> F1[Faculty A]
    CA1 --> D1[Departments A]

    CA2 --> S2[Students B]
    CA2 --> F2[Faculty B]
    CA2 --> D2[Departments B]

    CA3 --> S3[Students C]
    CA3 --> F3[Faculty C]
    CA3 --> D3[Departments C]
```

### How Isolation Works

| Role | Access Scope |
|------|-------------|
| **Super Admin** | All colleges, all students, all data — global view |
| **Staff Admin** | Only records created under their account (`created_by = self`) |
| **Student** | Only their own profile, attendance, and reports |

### Models with Tenant Isolation

The `created_by` foreign key is enforced across all core models:

```
Faculty      ──── created_by ──→ Admin User
Department   ──── created_by ──→ Admin User
Program      ──── created_by ──→ Admin User
Subject      ──── created_by ──→ Admin User
Profile      ──── created_by ──→ Admin User
```

Every queryset is automatically filtered by the logged-in admin's identity — a Staff Admin at College A can **never** access College B's students, subjects, or attendance records.

---

## 🔌 B2B REST API

A new programmatic API designed for **mobile clients (Flutter / Android / iOS)** to use LookIn AI's face recognition engine directly.

### Endpoint

```
POST /api/v1/get-face-encoding/
Authorization: Bearer <your-api-key>
Content-Type: application/json
```

### Request Payload

```json
{
  "frames": [
    "<base64-encoded-image-frame-1>",
    "<base64-encoded-image-frame-2>",
    "<base64-encoded-image-frame-3>"
  ]
}
```

> ⚠️ **Exactly 3 frames are required.** This enforces the liveness detection protocol. Requests with fewer or more frames are rejected.

### Response — Liveness Passed ✅

```json
{
  "liveness_passed": true,
  "embedding": [0.021, -0.134, 0.887, ...],
  "embedding_dimensions": 512,
  "model": "buffalo_l"
}
```

### Response — Liveness Failed ❌

```json
{
  "liveness_passed": false,
  "embedding": null,
  "reason": "Insufficient motion variance between frames. Possible spoofing attempt."
}
```

### Response — Auth Error 🔒

```json
{
  "error": "Unauthorized",
  "detail": "Invalid or inactive API key."
}
```

### Integration Flow (Flutter Example)

```
┌──────────────┐       3 frames (base64)        ┌─────────────────┐
│  Flutter App │  ──────────────────────────▶   │  LookIn AI API  │
│              │  ◀──────────────────────────   │  /api/v1/get-   │
│  512-D embed │       JSON response             │  face-encoding/ │
└──────────────┘                                 └─────────────────┘
        │
        ▼
  Local matching / cloud matching on mobile side
```

---

## 🔑 API Key Management

Admins can create and manage API keys directly from the admin dashboard — no manual database edits required.

### Key Generation

```python
# Secure random 64-character hex token
import secrets
api_key = secrets.token_hex(32)  # e.g. "a3f9b2c1d4e5..."
```

### APIKey Model

| Field | Type | Description |
|-------|------|-------------|
| `name` | CharField | Label for the API client (e.g., "Flutter App v1") |
| `key` | CharField | 64-char hex token — shown once on creation |
| `created_by` | ForeignKey | Admin who generated the key |
| `is_active` | BooleanField | Toggle to enable / disable the key |
| `created_at` | DateTimeField | Timestamp of key creation |
| `last_used_at` | DateTimeField | Last successful authenticated request |

### Authentication

All B2B API requests must include the key as a **Bearer token**:

```http
Authorization: Bearer a3f9b2c1d4e5f6...
```

Keys are validated against the `APIKey` table on every request — inactive keys are rejected with a `401 Unauthorized`.

---

## 📁 Project Structure

```
Face-Recognition-Attendance/
│
├── 📂 visionai/                    # Django project configuration
│   ├── __init__.py
│   ├── settings.py                 # Project settings (DB, Auth, Email, Cloudinary)
│   ├── urls.py                     # Root URL configuration
│   ├── wsgi.py                     # WSGI application entry point
│   └── asgi.py                     # ASGI application entry point
│
├── 📂 accounts/                    # Main application module
│   ├── __init__.py
│   ├── models.py                   # 14 database models (+ new APIKey model)
│   ├── views.py                    # 50+ view functions (3165+ lines)
│   ├── urls.py                     # 40+ URL patterns + new B2B API endpoints
│   ├── admin.py                    # Django admin configuration
│   ├── apps.py                     # App configuration
│   ├── signals.py                  # Auto-compute face encoding on profile save
│   │
│   ├── 🧠 encoding_service.py     # Core AI engine — InsightFace face recognition
│   ├── 🔍 face_detector.py        # Thin wrapper delegating to encoding_service
│   ├── ⚠️  yolo_detector.py       # DEPRECATED — stub for import compatibility
│   ├── 📊 session_buffer.py       # In-memory buffer + bulk DB write (psycopg2)
│   ├── 🛠️  utils.py               # Legacy recognition helper (InsightFace-backed)
│   ├── 🔐 backends.py             # Custom EmailBackend for email-based login
│   ├── 🔑 api_auth.py             # Bearer token API key authentication decorator
│   ├── 🌐 b2b_api.py              # B2B REST API views (/api/v1/get-face-encoding/)
│   │
│   ├── 📂 management/
│   │   └── 📂 commands/
│   │       ├── setup_google_auth.py       # Auto-configure Google OAuth credentials
│   │       ├── send_weekly_reports.py     # Weekly attendance summary email reports
│   │       └── create_default_superuser.py # Docker auto-provisioning superuser
│   │
│   ├── 📂 migrations/             # Django database migrations
│   │
│   ├── 📂 templates/              # HTML templates
│   │   ├── index.html              # Landing page
│   │   ├── login.html              # Student login (email-based)
│   │   ├── register.html           # Student registration with OTP
│   │   ├── verify_otp.html         # Email OTP verification page
│   │   ├── profile.html            # Student profile management
│   │   ├── attendance.html         # Student attendance log with filters
│   │   ├── report.html             # Student attendance analytics & charts
│   │   ├── header.html             # Shared navigation header
│   │   ├── live_scan.html          # Live webcam scanning interface
│   │   ├── password_reset.html     # Password reset flow pages
│   │   ├── password_reset_done.html
│   │   ├── password_reset_confirm.html
│   │   ├── password_reset_complete.html
│   │   │
│   │   ├── 📂 adminpanel/         # Admin-specific templates
│   │   │   ├── base.html           # Admin base layout with sidebar
│   │   │   ├── admin_login.html    # Admin login page
│   │   │   ├── admin_profile.html  # Admin profile management
│   │   │   ├── dashboard.html      # Student management dashboard
│   │   │   ├── attendance.html     # Photo/Video attendance upload
│   │   │   ├── attendance_history.html  # Attendance session history
│   │   │   ├── create_live_session.html # Live webcam session management
│   │   │   ├── compute_encodings.html   # Bulk face encoding recompute
│   │   │   ├── manage_enrollment.html   # Subject enrollment manager
│   │   │   ├── medical_leave.html       # Medical leave / proxy attendance
│   │   │   ├── api_keys.html       # API Key management dashboard  ← NEW
│   │   │   ├── subjects.html       # Subject CRUD (Core + Elective)
│   │   │   ├── faculties.html      # Faculty management
│   │   │   ├── departments.html    # Department management
│   │   │   ├── programs.html       # Program management
│   │   │   ├── semesters.html      # Semester management
│   │   │   └── divisions.html      # Division management
│   │   │
│   │   └── 📂 accounts/
│   │       └── my_attendance.html  # Student attendance summary
│   │
│   ├── 📂 static/                 # App-level static files
│   │   ├── style.css               # Custom styles
│   │   ├── logo.png                # Application logo
│   │   └── 📂 img/                # Static images
│   │       ├── logo.png
│   │       ├── logo1.png
│   │       ├── logo2.png
│   │       └── user.png            # Default user avatar
│   │
│   ├── tests.py                    # 7 test cases — core flow tests
│   ├── tests_complete.py           # Extended test suite
│   └── conftest.py                 # Test configuration / fixtures
│
├── 📂 attendance/                  # App placeholder (empty)
│
├── 📂 static/                      # Project-level static files
├── 📂 media/                       # User-uploaded files (gitignored)
├── 📂 profiles/                    # Profile images storage
│
├── 📄 manage.py                    # Django management entry point
├── 📄 requirements.txt             # Python dependencies
├── 📄 Dockerfile                   # Docker container configuration
├── 📄 entrypoint.sh                # Docker entrypoint (migrate + collectstatic + superuser + gunicorn)
├── 📄 build.sh                     # Build script for deployment (Render)
├── 📄 .env                         # Environment variables (gitignored)
├── 📄 .gitignore                   # Git ignore rules
└── 📄 test_speed.py                # Performance benchmarking script
```

---

## 📊 Database Models

```mermaid
erDiagram
    User ||--|| Profile : has
    User ||--o{ Attendance : records
    User ||--o{ SubjectEnrollment : enrolls
    User ||--o{ LiveAttendanceRecord : scans
    User ||--o{ LiveAttendanceSession : creates
    User ||--o{ APIKey : owns

    Faculty ||--o{ Subject : teaches
    Department ||--o{ Subject : belongs_to
    Program ||--o{ Subject : core_program
    Semester ||--o{ Subject : core_semester

    Subject ||--o{ SubjectEnrollment : has
    Subject ||--o{ AttendanceSession : tracked_in
    Subject ||--o{ LiveAttendanceSession : live_tracked_in
    Subject ||--o{ SubjectProgramSemester : elective_pairs

    AttendanceSession ||--o{ Attendance : contains
    LiveAttendanceSession ||--o{ LiveAttendanceRecord : contains

    Subject }o--o{ Division : core_divisions
    Subject }o--o{ Program : elective_programs
    Subject }o--o{ Semester : elective_semesters

    Profile {
        string mobile
        string roll
        string faculty_name
        string department_name
        string program_name
        string semester_name
        string division_name
        string photo_url
        string face_encoding_b64
        datetime encoding_updated_at
        int created_by_id
    }

    APIKey {
        string name
        string key
        int is_active
        datetime created_at
        datetime last_used_at
        int created_by_id
    }

    Subject {
        string name
        string course_code
        string subject_type
        int created_by_id
    }

    Attendance {
        int status
        string time_marked
    }

    LiveAttendanceRecord {
        datetime scanned_at
        float confidence
    }
```

### Model Summary

| Model | Description |
|-------|-------------|
| `Faculty` | Faculty/Professor entity — isolated by `created_by` |
| `Department` | Academic department — isolated by `created_by` |
| `Program` | Academic program (BTech, MTech, etc.) — isolated by `created_by` |
| `Semester` | Semester identifier |
| `Division` | Class division (A, B, C, etc.) |
| `Subject` | Subject with type (Core / Elective) — isolated by `created_by` |
| `SubjectProgramSemester` | Elective subject ↔ (Program, Semester) mapping |
| `SubjectEnrollment` | Student enrollment in a specific subject |
| `Lecture` | Lecture slot definition |
| `AttendanceSession` | Permanent attendance session record (photo/video/live) |
| `Attendance` | Individual student attendance record (Present/Absent) |
| `Profile` | Extended user profile with face encoding (512-d float32 binary) — isolated by `created_by` |
| `LiveAttendanceSession` | Real-time live webcam scanning session |
| `LiveAttendanceRecord` | Individual live scan record with confidence score |
| `APIKey` | **NEW** — B2B API key with Bearer token, active flag, last-used tracking |

---

## 🔗 API Endpoints

### Authentication & User Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET/POST` | `/register/` | Student registration with email OTP |
| `POST` | `/verify-otp/` | OTP verification |
| `GET/POST` | `/login/` | Student login (**email-based** — not username) |
| `GET` | `/logout/` | Logout |
| `GET/POST` | `/profile/` | Student profile management |
| `POST` | `/reset_password/` | Password reset via email |

### Admin Panel

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET/POST` | `/admin-login/` | Admin authentication |
| `GET/POST` | `/admin-dashboard/` | Student CRUD + Bulk register |
| `POST` | `/admin-dashboard/bulk-register/` | CSV + ZIP bulk student import |
| `POST` | `/admin-dashboard/bulk-delete/` | Bulk student deletion |
| `GET/POST` | `/admin-dashboard/compute-encodings/` | Recompute all face encodings |
| `GET/POST` | `/admin-dashboard/live-sessions/` | Create & manage live webcam sessions |
| `GET/POST` | `/admin-dashboard/api-keys/` | **NEW** — Manage B2B API keys |
| `POST` | `/admin-dashboard/api-keys/create/` | **NEW** — Generate new API key |
| `POST` | `/admin-dashboard/api-keys/<id>/toggle/` | **NEW** — Enable/disable an API key |
| `POST` | `/admin-dashboard/api-keys/<id>/delete/` | **NEW** — Delete an API key |

### 🆕 B2B REST API (v1)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/get-face-encoding/` | Bearer Token | Submit 3 base64 frames → get 512-D embedding + liveness result |

### Attendance System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET/POST` | `/mark-attendance/` | Upload group photo or video for attendance |
| `GET` | `/attendance-history/` | View all attendance sessions with filters |
| `GET` | `/download-attendance/<id>/` | Download Excel (.xlsx) report |
| `GET` | `/attendance/` | Student attendance log |
| `GET` | `/report/` | Student analytics dashboard with trend charts |
| `GET` | `/my-attendance/` | Monthly attendance calendar view |

### Live Webcam Scan API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/live-scan/` | Submit webcam frame for face recognition |
| `GET` | `/api/live-session/<id>/status/` | Get live session scan count & student list |
| `POST` | `/api/live-session/<id>/close/` | Close live session & transfer to permanent log |

### Subject Enrollment API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/subject-enrollment/` | Enrollment management page |
| `GET` | `/api/subject-context/<id>/` | Get subject details (program, semester, divisions) |
| `GET` | `/api/eligible-students/<id>/` | Get eligible students for enrollment |
| `POST` | `/api/enroll-student/` | Enroll single student via AJAX |
| `POST` | `/api/bulk-enroll-preview/<id>/` | CSV bulk enrollment preview with validation |
| `POST` | `/api/bulk-enroll-confirm/<id>/` | Confirm bulk enrollment (atomic transaction) |
| `POST` | `/api/remove-enrollment/<id>/` | Remove individual enrollment |

### Academic Entity CRUD

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET/POST` | `/faculties/` | Faculty management (tenant-isolated) |
| `GET/POST` | `/departments/` | Department management (tenant-isolated) |
| `GET/POST` | `/programs/` | Program management (tenant-isolated) |
| `GET/POST` | `/semesters/` | Semester management |
| `GET/POST` | `/divisions/` | Division management |
| `GET/POST` | `/subjects/` | Subject management (tenant-isolated) |

### Miscellaneous

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/attendance-progress/` | Real-time processing progress (photo/video upload) |
| `POST` | `/grant-medical-leave/` | Grant medical/proxy leave |

---

## ⚙️ Tech Stack

<div align="center">

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | ![Django](https://img.shields.io/badge/Django-5.2-092E20?style=flat-square&logo=django) | Web framework, ORM, Auth |
| **AI Engine** | ![InsightFace](https://img.shields.io/badge/InsightFace-buffalo__l-FF6F61?style=flat-square) | Face detection & recognition |
| **Computer Vision** | ![OpenCV](https://img.shields.io/badge/OpenCV-4.x-5C3EE8?style=flat-square&logo=opencv) | Image/Video preprocessing |
| **ML Runtime** | ![ONNX](https://img.shields.io/badge/ONNX_Runtime-1.x-005CED?style=flat-square) | Model inference (CPU/CUDA) |
| **Database** | ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-NeonDB-4169E1?style=flat-square&logo=postgresql) | Production database |
| **Database (Dev)** | ![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat-square&logo=sqlite) | Development database |
| **File Storage** | ![Cloudinary](https://img.shields.io/badge/Cloudinary-CDN-3448C5?style=flat-square&logo=cloudinary) | Media file hosting (profile photos) |
| **Auth** | ![Google](https://img.shields.io/badge/Google_OAuth-2.0-4285F4?style=flat-square&logo=google) | Social login via django-allauth |
| **Auth Backend** | ![Email](https://img.shields.io/badge/Custom-EmailBackend-EA4335?style=flat-square&logo=gmail) | Email-based authentication |
| **B2B API Auth** | ![Bearer](https://img.shields.io/badge/Bearer-Token_Auth-f59e0b?style=flat-square&logo=jsonwebtokens) | API key authentication |
| **Email** | ![Gmail](https://img.shields.io/badge/Gmail_SMTP-587-EA4335?style=flat-square&logo=gmail) | Absent alerts & OTP verification |
| **Server** | ![Gunicorn](https://img.shields.io/badge/Gunicorn-WSGI-499848?style=flat-square&logo=gunicorn) | Production WSGI server |
| **Static** | ![WhiteNoise](https://img.shields.io/badge/WhiteNoise-Static-lightgrey?style=flat-square) | Static file serving |
| **Container** | ![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=flat-square&logo=docker) | Containerized deployment |
| **Reporting** | ![Excel](https://img.shields.io/badge/openpyxl-Excel-217346?style=flat-square&logo=microsoftexcel) | Excel report generation |
| **PDF** | ![ReportLab](https://img.shields.io/badge/ReportLab-PDF-DC143C?style=flat-square) | PDF report generation |

</div>

---

## 🛠️ Installation & Setup

### Prerequisites

- **Python 3.10+**
- **pip** (Python package manager)
- **Git**

### 1. Clone the Repository

```bash
git clone https://github.com/nensiandani/Face-Recognition-Attendance.git
cd Face-Recognition-Attendance
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True

# Email (Gmail SMTP)
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password

# Cloudinary (Media Storage)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Google OAuth 2.0
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Database (Optional — defaults to SQLite)
DATABASE_URL=postgresql://user:pass@host/dbname?sslmode=require

# Docker superuser auto-provisioning (Optional)
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=yourpassword
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Create Superuser (Admin)

```bash
python manage.py createsuperuser
```

### 7. Collect Static Files

```bash
python manage.py collectstatic --no-input
```

### 8. Start the Development Server

```bash
python manage.py runserver
```

> 🌐 Open http://localhost:8000 in your browser

---

## 🐳 Docker Deployment

### Build and Run

```bash
# Build the Docker image
docker build -t lookin-ai .

# Run the container
docker run -p 8000:8000 \
  -e SECRET_KEY=your-secret-key \
  -e DATABASE_URL=your-database-url \
  -e CLOUDINARY_CLOUD_NAME=your-cloud-name \
  -e CLOUDINARY_API_KEY=your-api-key \
  -e CLOUDINARY_API_SECRET=your-secret \
  -e EMAIL_USER=your-email \
  -e EMAIL_PASS=your-app-password \
  -e DJANGO_SUPERUSER_EMAIL=admin@example.com \
  -e DJANGO_SUPERUSER_PASSWORD=yourpassword \
  lookin-ai
```

### Dockerfile Breakdown

```dockerfile
FROM python:3.10-slim
# Installs build tools (cmake, gcc) for native dependencies
# Installs dlib-bin separately for optimized build caching
# Uses multi-layer RUN for efficient Docker layer caching
# Entrypoint: migrate → collectstatic → setup_google_auth
#           → create_default_superuser (NEW) → gunicorn
```

> 🆕 The `create_default_superuser` management command auto-provisions a superuser on first boot using `DJANGO_SUPERUSER_EMAIL` and `DJANGO_SUPERUSER_PASSWORD` — no manual `createsuperuser` step required in production.

---

## 🔐 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | ✅ | Django secret key for cryptographic signing |
| `DEBUG` | ❌ | Enable debug mode (default: `True`) |
| `DATABASE_URL` | ❌ | PostgreSQL connection string (fallback: SQLite) |
| `EMAIL_USER` | ✅ | Gmail address for SMTP |
| `EMAIL_PASS` | ✅ | Gmail App Password (not regular password) |
| `CLOUDINARY_CLOUD_NAME` | ✅ | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | ✅ | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | ✅ | Cloudinary API secret |
| `GOOGLE_CLIENT_ID` | ❌ | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | ❌ | Google OAuth client secret |
| `SITE_DOMAIN` | ❌ | Domain for email links (default: `localhost:8000`) |
| `DJANGO_SUPERUSER_EMAIL` | ❌ | Auto-create superuser on Docker boot (NEW) |
| `DJANGO_SUPERUSER_PASSWORD` | ❌ | Auto-create superuser password on Docker boot (NEW) |

---

## 🧪 Testing

The project includes **7 critical test cases** covering the core attendance system logic:

```bash
# Run all tests
python manage.py test accounts

# Run specific test class
python manage.py test accounts.tests.TestFaceEncodingRoundtrip
```

### Test Coverage

| # | Test | What It Verifies |
|---|------|-----------------|
| 1 | **Face Encoding Roundtrip** | `set_face_encoding()` → DB → `get_face_encoding()` returns identical 512-d array |
| 2 | **Division Check** | Wrong-division students are excluded from core subject absent list |
| 3 | **Enrollment Check** | Non-enrolled students are blocked from attendance |
| 4 | **Absent Email** | Emails sent ONLY to absent students |
| 5 | **Present Zero Email** | All-present scenario sends zero emails |
| 6 | **Excel Download** | `.xlsx` file has correct headers, data, and subject codes |
| 7 | **Attendance Percentage** | Percentage calculation: 100%, 75%, 0%, below-threshold, zero-total |

> ⚡ Tests mock InsightFace (`buffalo_l` model) to avoid loading 500MB model weights during CI

---

## 📱 User Roles & Workflows

### 👨‍🎓 Student Workflow

```mermaid
graph LR
    A[Register] -->|OTP Email| B[Verify OTP]
    B --> C[Login via Email]
    C --> D[Complete Profile]
    D -->|Upload Photo| E[Auto Face Encoding]
    E --> F[View Attendance]
    F --> G[View Report]
    G --> H[Download Report]
```

**Student can:**
- Register with email OTP verification or Google OAuth
- Log in using their **email address** (not username)
- Upload profile photo (face encoding auto-computed via Django signal)
- View attendance log with date range & subject filters
- View analytics dashboard with cumulative trend charts
- Reset password via email link

---

### 👨‍🏫 Admin / Professor Workflow

```mermaid
graph LR
    A[Admin Login] --> B[Dashboard]
    B --> C{Attendance Mode}
    C -->|Upload Photo| D[Group Photo]
    C -->|Upload Video| E[Video Recording]
    C -->|Webcam| F[Live Scan Session]
    D --> G[Auto Face Recognition]
    E --> G
    F --> H[Students Scan Face Live]
    G --> I[Mark Present/Absent]
    H --> I
    I --> J[Send Absent Emails]
    I --> K[Download Excel Report]
    B --> L[Manage API Keys]
    L --> M[B2B Mobile Client Access]
```

**Admin can:**
- Manage students (add, edit, delete, bulk CSV+ZIP import) — **scoped to their college only**
- Manage academic hierarchy (Faculty → Department → Program → Semester → Division → Subject) — **tenant-isolated**
- Mark attendance via **3 modes**: Group Photo upload, Video upload, Live Webcam session
- Manage subject enrollments (individual + CSV bulk enrollment with preview)
- View attendance history with subject & date filters
- Download attendance reports as Excel (.xlsx)
- Compute/recompute face encodings for all students
- Grant medical leave / proxy attendance
- Create and close live sessions (auto-transfers to permanent attendance log)
- **NEW** — Generate and manage B2B API keys for mobile/Flutter integrations

---

### 🔌 B2B Mobile Client Workflow

```mermaid
graph LR
    A[Admin creates API Key] --> B[Mobile App receives key]
    B --> C[Capture 3 frames via camera]
    C --> D[POST /api/v1/get-face-encoding/]
    D --> E{Liveness Check}
    E -->|Pass| F[Return 512-D embedding]
    E -->|Fail| G[Return liveness_passed: false]
    F --> H[App does matching locally]
```

---

## 📈 Performance Optimizations

| # | Optimization | Description |
|---|-------------|-------------|
| **OPT 1** | Smart Video Sampling | Process every 50th frame instead of every frame |
| **OPT 2** | Frame Preprocessing | Resize to max 640px before AI processing |
| **OPT 3** | Encoding Cache | In-memory cache with 5-minute TTL (avoids DB hits) |
| **OPT 4** | Batch Face Matching | NumPy vectorized dot-product for fast similarity computation |
| **OPT 5** | Thread Pool | `ThreadPoolExecutor(max_workers=4)` for parallel file processing |
| **OPT 6** | Progress Tracking | Real-time session-based progress API for UI feedback |
| **OPT 7** | SessionBuffer | Bulk DB write via `psycopg2.execute_values()` — single INSERT |
| **OPT 8** | Model Singleton | InsightFace loaded ONCE at startup (thread-safe lazy init) |
| **OPT 9** | Minimal Modules | Only `detection + recognition` modules loaded (not genderage/landmark) |
| **OPT 10** | Early Exit | Stop video processing once all enrolled students are confirmed |
| **OPT 11** | Background Threads | Email sending and face encoding run in daemon threads |
| **OPT 12** | Tenant Query Filter | All admin querysets pre-filtered by `created_by` — zero cross-tenant DB leakage |
| **OPT 13** | API Key Cache | Active API keys cached to avoid repeated DB lookups on every B2B request |

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:6366f1,50:8b5cf6,100:06b6d4&height=120&section=footer&animation=fadeIn" width="100%" />

<br />

**Built with ❤️ by Nensi Andani & Jaimeen Chauhan**

<br />

<a href="#"><img src="https://img.shields.io/badge/⭐_Star_This_Repo-If_You_Found_It_Useful!-yellow?style=for-the-badge" /></a>

<br /><br />

<img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&weight=500&size=18&duration=4000&pause=2000&color=6366F1&center=true&vCenter=true&width=600&lines=Thank+you+for+visiting+LookIn+AI+🚀;Now+with+Multi-Tenant+SaaS+%26+B2B+API!" alt="Footer" />

</div>
