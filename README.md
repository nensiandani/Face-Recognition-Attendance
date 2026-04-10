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
</p>

<!-- Animated Typing -->
<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&weight=600&size=24&duration=3000&pause=1000&color=8B5CF6&center=true&vCenter=true&multiline=true&repeat=true&width=700&height=100&lines=🎯+Real-Time+Face+Recognition+Attendance;📸+Group+Photo+%2B+Video+%2B+Live+Webcam;🤖+Powered+by+InsightFace+Buffalo_L+Model" alt="Typing SVG" /></a>

<br />

<!-- Stats -->
<img src="https://img.shields.io/badge/Accuracy-95%25+-brightgreen?style=flat-square" />
<img src="https://img.shields.io/badge/Processing-<3s_per_photo-blue?style=flat-square" />
<img src="https://img.shields.io/badge/Models-512D_Embeddings-purple?style=flat-square" />

</div>

---

## 📋 Table of Contents

<details>
<summary>Click to expand</summary>

- [✨ Overview](#-overview)
- [🚀 Key Features](#-key-features)
- [🏗️ System Architecture](#️-system-architecture)
- [🧠 AI Pipeline](#-ai-pipeline)
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
└─────────────────────────────────────────────────────────────────┘
```

</div>

**LookIn AI** eliminates the tedious manual roll-call process by leveraging deep learning-based face recognition. Teachers can simply upload a **group photo**, record a **video** of the classroom, or start a **live webcam session** — and the system automatically identifies students, marks attendance, sends email notifications to absentees, and generates downloadable Excel reports.

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

</td>
<td width="50%">

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
- Email OTP verification on registration
- Strong password enforcement (8+ chars, uppercase, lowercase, digit, special)
- Google OAuth 2.0 social login
- CSRF protection on all form endpoints
- Admin-only access control with session guard

</td>
</tr>
</table>

---

## 🏗️ System Architecture

```mermaid
graph TB
    subgraph Client["🌐 Client Layer"]
        A[👨‍🏫 Admin Panel] --> |Upload Photo/Video| B
        C[📹 Live Scan Page] --> |Webcam Frame| B
        E[👨‍🎓 Student Portal] --> |View Attendance| B
    end

    subgraph Server["⚙️ Django Backend"]
        B[URL Router] --> F[Views Layer]
        F --> G[Encoding Service]
        F --> H[Session Buffer]
        F --> I[Email Service]
    end

    subgraph AI["🧠 AI Engine"]
        G --> J[InsightFace buffalo_l]
        J --> K[Face Detection]
        J --> L[512-D Embedding]
        L --> M[Cosine Similarity Matching]
    end

    subgraph Storage["💾 Data Layer"]
        H --> N[(PostgreSQL / SQLite)]
        F --> O[Cloudinary CDN]
        G --> P[In-Memory Cache]
    end

    style Client fill:#f0f4ff,stroke:#6366f1
    style Server fill:#fef3f2,stroke:#ef4444
    style AI fill:#ecfdf5,stroke:#10b981
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
│ Video    │    │ Unsharp  │    │  RetinaFace  │    │  ArcFace    │    │ Sim > θ  │
└──────────┘    └──────────┘    └──────────────┘    └─────────────┘    └──────────┘
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
# Pixel-diff on 64×64 downsampled grayscale frames
# Requires 3-5 frames captured ~300ms apart
# Variance threshold: 1.8 (prevents photo/screen attacks)
# Processing time: < 0.1s total
```

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
│   ├── models.py                   # 13 database models (User, Profile, Attendance, etc.)
│   ├── views.py                    # 50+ view functions (3165 lines)
│   ├── urls.py                     # 40+ URL patterns with REST API endpoints
│   ├── admin.py                    # Django admin configuration
│   ├── apps.py                     # App configuration
│   ├── signals.py                  # Auto-compute face encoding on profile save
│   │
│   ├── 🧠 encoding_service.py     # Core AI engine — InsightFace face recognition
│   ├── 🔍 face_detector.py        # Thin wrapper delegating to encoding_service
│   ├── ⚠️  yolo_detector.py       # DEPRECATED — stub for import compatibility
│   ├── 📊 session_buffer.py       # In-memory buffer + bulk DB write (psycopg2)
│   ├── 🛠️  utils.py               # Legacy recognition helper (InsightFace-backed)
│   │
│   ├── 📂 management/
│   │   └── 📂 commands/
│   │       ├── setup_google_auth.py    # Auto-configure Google OAuth credentials
│   │       └── send_weekly_reports.py  # Weekly attendance summary email reports
│   │
│   ├── 📂 migrations/             # Django database migrations
│   │
│   ├── 📂 templates/              # HTML templates
│   │   ├── index.html              # Landing page
│   │   ├── login.html              # Student login
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
│   ├── 1.jpeg, 2.jpeg              # Sample images
│   └── 3.mp4                       # Sample video
│
├── 📂 media/                       # User-uploaded files (gitignored)
│   ├── 📂 attendance/             # Uploaded attendance photos/videos
│   └── 📂 profiles/              # Student profile photos
│
├── 📂 profiles/                    # Profile images storage
│
├── 📄 manage.py                    # Django management entry point
├── 📄 requirements.txt             # Python dependencies
├── 📄 Dockerfile                   # Docker container configuration
├── 📄 entrypoint.sh                # Docker entrypoint (migrate + collectstatic + gunicorn)
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
        string faculty
        string department
        string program
        string semester
        string division
        image image
        binary face_encoding
        datetime encoding_updated_at
    }

    Subject {
        string name
        string course_code
        enum subject_type
    }

    Attendance {
        boolean status
        time time_marked
    }

    LiveAttendanceRecord {
        datetime scanned_at
        float confidence
    }
```

### Model Summary

| Model | Description |
|-------|-------------|
| `Faculty` | Faculty/Professor entity with name and short code |
| `Department` | Academic department |
| `Program` | Academic program (BTech, MTech, etc.) |
| `Semester` | Semester identifier |
| `Division` | Class division (A, B, C, etc.) |
| `Subject` | Subject with type (Core / Elective), linked to Faculty & Department |
| `SubjectProgramSemester` | Elective subject ↔ (Program, Semester) mapping |
| `SubjectEnrollment` | Student enrollment in a specific subject |
| `Lecture` | Lecture slot definition |
| `AttendanceSession` | Permanent attendance session record (photo/video/live) |
| `Attendance` | Individual student attendance record (Present/Absent) |
| `Profile` | Extended user profile with face encoding (512-d float32 binary) |
| `LiveAttendanceSession` | Real-time live webcam scanning session |
| `LiveAttendanceRecord` | Individual live scan record with confidence score |

---

## 🔗 API Endpoints

### Authentication & User Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET/POST` | `/register/` | Student registration with email OTP |
| `POST` | `/verify-otp/` | OTP verification |
| `GET/POST` | `/login/` | Student login |
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
| `GET/POST` | `/faculties/` | Faculty management (name + code) |
| `GET/POST` | `/departments/` | Department management |
| `GET/POST` | `/programs/` | Program management |
| `GET/POST` | `/semesters/` | Semester management |
| `GET/POST` | `/divisions/` | Division management |
| `GET/POST` | `/subjects/` | Subject management (Core + Elective with program-semester pairs) |

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
  lookin-ai
```

### Dockerfile Breakdown

```dockerfile
FROM python:3.10-slim
# Installs build tools (cmake, gcc) for native dependencies
# Installs dlib-bin separately for optimized build caching
# Uses multi-layer RUN for efficient Docker layer caching
# Entrypoint: migrate → collectstatic → setup_google_auth → gunicorn
```

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
    B --> C[Login]
    C --> D[Complete Profile]
    D -->|Upload Photo| E[Auto Face Encoding]
    E --> F[View Attendance]
    F --> G[View Report]
    G --> H[Download Report]
```

**Student can:**
- Register with email OTP verification or Google OAuth
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
```

**Admin can:**
- Manage students (add, edit, delete, bulk CSV+ZIP import)
- Manage academic hierarchy (Faculty → Department → Program → Semester → Division → Subject)
- Mark attendance via **3 modes**: Group Photo upload, Video upload, Live Webcam session
- Manage subject enrollments (individual + CSV bulk enrollment with preview)
- View attendance history with subject & date filters
- Download attendance reports as Excel (.xlsx)
- Compute/recompute face encodings for all students
- Grant medical leave / proxy attendance
- Create and close live sessions (auto-transfers to permanent attendance log)

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

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:6366f1,50:8b5cf6,100:06b6d4&height=120&section=footer&animation=fadeIn" width="100%" />

<br />

**Built with ❤️ by Nensi Andani & Jaimeen Chauhan**

<br />

<a href="#"><img src="https://img.shields.io/badge/⭐_Star_This_Repo-If_You_Found_It_Useful!-yellow?style=for-the-badge" /></a>

<br /><br />

<img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&weight=500&size=18&duration=4000&pause=2000&color=6366F1&center=true&vCenter=true&width=500&lines=Thank+you+for+visiting+LookIn+AI+🚀" alt="Footer" />

</div>
