# Clinic Management System

A Django-based multi-tenant clinic management system with role-based access control for managing patient appointments, diagnoses, prescriptions, and medical records.

---

## 📋 Features

### 👥 User Roles & Access

The system supports **4 user roles** with distinct functionalities:

#### 1. **Patient**
- View personal appointment history
- Book and manage appointments
- Receive diagnoses from doctors
- Access prescriptions and medical requirements
- Passwordless login (using phone + username)
- View appointment details and medical records

#### 2. **Doctor**
- View all patients in the clinic
- Manage patient appointments
- Create and update patient diagnoses
- Prescribe medications and treatment requirements
- Track appointment history for each patient
- Staff login with authentication

#### 3. **Reception**
- Create and register new patients
- Schedule and manage appointments
- Update appointment statuses
- View today's appointment dashboard
- Handle patient registrations


### 🎯 Core Features

#### **Appointment Management**
- Schedule appointments with specific dates
- Track appointment costs
- Mark appointments as Pending, Completed, or Canceled
- Priority appointment handling (prior flag)
- Appointment history tracking
- Auto-ordering by creation date

#### **Medical Records**
- **Diagnosis**: Store and update patient diagnoses per appointment
- **Prescriptions**: Add medication instructions per appointment
- **Requirements**: Track medical test/treatment requirements
- One-to-one relationship with appointments for each record type

#### **Dashboard & Analytics**
- Reception dashboard with today's appointments
- Patient appointment overview
- Doctor patient list with next appointment info
- Cached dashboard data for performance (15-minute TTL)
- Appointment status visualization

#### **Security & Access Control**
- Role-based permission system (`@staff_required`, `@doctor_required`, `@user_owns_profile`)
- Account lockout after failed login attempts (15 attempts = 15-minute lock)
- Phone number validation for authentication
- CSRF protection
- Session management

#### **Multi-Tenant Architecture**
- Complete tenant isolation using django-tenants
- Separate databases per Doctor (schema-based)
- Tenant-specific domain routing
- Public schema for authentication routing

---

## 🛠️ Technology Stack

### **Backend**
- **Django** (4.2.26) - Web framework
- **PostgreSQL** (15-alpine) - Database
- **Redis** (7) - Caching and session storage

### **Authentication & Authorization**
- Django Authentication (custom User model)
- Phone number field support (Egyptian region)
- django-tenants (3.9.0) - Multi-tenant support

### **Additional Libraries**
- **django-redis** (6.0.0) - Redis cache backend
- **django-debug-toolbar** (6.1.0) - Development debugging
- **psycopg** (3.2.13) - PostgreSQL adapter
- **phonenumbers** (9.0.19) - Phone validation
- **python-decouple** (3.8) - Environment variables

### **Frontend**
- HTML5/CSS3 (Django Templates)
- HTMX integration
- Django Template Tags (custom navigation)

### **Deployment**
- Docker & Docker Compose
- Volume management for data persistence
- Environment-based configuration (.env)

---

## 📊 Data Models

### **User Model** (Extended Django AbstractUser)
```
User
├── username (unique, allows spaces)
├── phone (unique, validates Egyptian numbers)
├── role (admin, doctor, reception, patient)
├── failed_login_attempts (security)
├── account_locked_until (lockout management)
└── is_staff_member (computed property)
```

### **Patient Model**
```
Patient
├── user (OneToOne → User)
├── age (0-100)
├── appointments (reverse relation → Appointment)
├── created_at
└── updated_at
```

### **Appointment Model**
```
Appointment
├── date (appointment date)
├── cost (integer, validated ≥ 0)
├── status (Completed, Pending, Canceled)
├── is_prior (priority flag)
├── patient (ForeignKey → Patient)
├── diagnosis (reverse OneToOne → Diagnosis)
├── prescription (reverse OneToOne → Prescription)
├── requires (reverse OneToOne → Requires)
└── created_at
```

### **Medical Records**
- **Diagnosis**: Text diagnosis (max 200 chars), links to Appointment
- **Prescription**: Medication instructions (max 100 chars)
- **Requires**: Test/treatment requirements (max 100 chars)

---

## 🔄 Data Flow

### **Patient Login Flow**

1. **Patient Accesses System**
   - Visits public landing page (public schema)
   - Navigates to patient login

2. **Authentication**
   - Enters **phone** (registered phone number)
   - Enters **username** (credentials)
   - System validates credentials via `authenticate()`
   - Checks if account is locked (failed attempts > 15)

3. **Session Creation**
   - User session created in tenant schema
   - Django session middleware tracks authentication
   - Redis stores session data

4. **Dashboard Access**
   - Redirected to patient profile (route: `/patient/patient-profile/<user_id>/`)
   - View personal appointments
   - Click appointment to see details
   - Medical records (diagnosis, prescription, requirements) attached to appointments

5. **Accessing Medical Records**
   - Patient views appointment details
   - Doctor can create/update diagnosis for appointment
   - Medical records displayed in appointment details view

### **Staff (Doctor/Reception) Login Flow**

1. **Access Staff Portal**
   - Visits domain-specific login page
   - Enters **username** and **password**

2. **Authentication**
   - System validates credentials
   - Checks account lockout status
   - Verifies user is staff member (`is_staff_member` property)

3. **Tenant Routing**
   - System identifies tenant (doctor or reception's associated doctor)
   - Finds primary domain for the tenant
   - Creates session in tenant schema

4. **Dashboard Access**
   - Redirected to reception/dashboard
   - Doctor views patients list with next appointment dates
   - Reception views today's appointments
   - Can create/manage appointments and patient records

### **Appointment Management Flow**

1. **Reception Creates Appointment**
   - Route: `/reception/create-appointment/<patient_id>/`
   - Sets date, cost, and priority
   - System validates date (cannot be in past)
   - Appointment stored with "Pending" status

2. **Doctor Manages Appointment**
   - Views appointment in dashboard
   - After consultation: creates/updates diagnosis
   - Prescribes medication and requirements
   - Updates status to "Completed" or "Canceled"

3. **Patient Views Results**
   - Logs into patient portal
   - Navigates to appointment details
   - Sees diagnosis, prescription, and requirements
   - Records immutable once saved

### **Appointment Creation Redirect Solution**

**Problem**: When creating an appointment from patient profile or appointment details pages, the system always redirected to dashboard instead of returning to the originating page.

**Solution Implementation**:

1. **Added `next_url` Parameter to Form** (`common/shared_forms.py`)
   - Added hidden `next_url` field to `CreateAppointmentForm`
   - This field captures the return URL and passes it through form submission
   - Hidden field prevents user from seeing/modifying the redirect target

2. **Updated View to Handle Redirects** (`reception/views.py`)
   - Modified `create_appointment()` view to extract `next` parameter from GET request
   - Falls back to `next_url` from POST data if GET parameter not present
   - Passes `next_url` to template context for form rendering
   - Checks if `next_url` exists after form submission:
     - If provided: redirects to the originating page
     - If not provided: falls back to dashboard (default behavior)

3. **Updated Form Template** (`reception/templates/reception/add_appointment.html`)
   - Modified form loop to handle the hidden `next_url` field separately
   - Renders hidden field without displaying a label
   - Field automatically submits with form data

4. **Updated Calling Templates**
   - **Patient Profile** (`patient/templates/patient/patient_profile.html`):
     - "موعد جديد" button now passes `?next={% url 'patient-profile' user_id %}`
     - User returns to patient profile after appointment creation
   
   - **Appointment Details** (`patient/templates/patient/appointment_details.html`):
     - "إضافة موعد مستقبلي" button passes `?next={% url 'appointment-details' appointment.id user_id %}`
     - User returns to appointment details after new appointment creation

**Result**: 
- Patient Profile → Create Appointment → Returns to Patient Profile ✓
- Appointment Details → Create Appointment → Returns to Appointment Details ✓
- Direct access to create appointment → Returns to Dashboard ✓

### **Caching & Performance**

- **Dashboard Cache** (15 minutes)
  - Reception dashboard caches today's appointments
  - Tenant-specific cache keys: `clinic:{tenant_id}:{cache_type}`
  - Cache invalidated on appointment changes

- **Session Storage**
  - Redis stores user sessions
  - Distributed session access across servers
  - Auto-expires after configured TTL

---

## 🚀 Getting Started

### **Prerequisites**
- Docker & Docker Compose
- `.env` file with database credentials

### **Installation**

```bash
# Clone repository
git clone <repository-url>
cd clinic_system_docker

# Create environment file
cp .env.example .env

# Build and start containers
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Access system
# Admin: http://localhost:8001
# Patient Portal: http://<tenant-domain>:8001
```

### **Directory Structure**
```
clinic_system_docker/
├── clinic_system/          # Main Django project
│   ├── settings.py         # Configuration
│   ├── urls.py             # URL routing
│   ├── celery.py           # Task queue (if used)
│   ├── redis.py            # Redis configuration
│   └── wsgi.py
├── doctor/                 # Doctor/Staff module
│   ├── models.py           # User, Doctor models
│   ├── views.py            # Doctor dashboard
│   ├── views_auth.py       # Staff authentication
│   └── urls.py
├── patient/                # Patient module
│   ├── models.py           # Patient, Appointment, Diagnosis
│   ├── views.py            # Patient views & medical records
│   ├── views_auth.py       # Patient authentication
│   └── urls.py
├── reception/              # Reception module
│   ├── models.py           # Reception staff model
│   ├── views.py            # Appointment management
│   ├── views_auth.py       # Reception authentication
│   └── urls.py
├── common/                 # Shared utilities
│   ├── permissions.py      # Decorators for access control
│   ├── shared_forms.py     # Common forms
│   └── templatetags/       # Custom template filters
├── static/                 # CSS, JS files
├── templates/              # HTML templates
├── docker-compose.yml      # Docker setup
├── Dockerfile              # Container definition
├── manage.py               # Django management
└── requirements.txt        # Python dependencies
```

---

## 🔐 Authentication Methods

| Role      | Method             | Fields                  | Notes                 |
|-----------|------------------|------------------------|----------------------|
| Patient   | Passwordless     | Phone + Username       | No password required  |
| Doctor    | Password         | Username + Password    | Staff authentication  |
| Reception | Password         | Username + Password    | Staff authentication  |
| Admin     | Password         | Username + Password    | Full system access    |

---

## 🎨 UI Components

### **Templates**
- **Public**: Landing page, authentication portals
- **Doctor**: Patient list, appointments, financial records
- **Patient**: Profile, appointments, medical records
- **Reception**: Appointment creation, dashboard, patient management

### **Responsive Design**
- Bootstrap-based responsive layout
- Print stylesheets for reports
- HTMX for dynamic updates without page reload
- Custom navigation based on user role

---

## 📝 API Endpoints Summary

### **Patient Routes** (`/patient/`)
- `patient-signup/` - Register new patient
- `patient-login/` - Patient authentication
- `patient-profile/<user_id>/` - View appointments
- `appointment-details/<appoint_id>/<user_id>/` - Appointment details
- `add-diagnosis/`, `update-diagnosis/`, `view-diagnosis/`, `delete-diagnosis/`
- `add-prescription/`, `update-prescription/`, `view-prescription/`, `delete-prescription/`
- `add-requires/`, `update-requires/`, `view-requires/`, `delete-requires/`

### **Doctor Routes** (`/doctor/`)
- `staff-login/` - Staff authentication
- `staff-logout/` - Logout
- `patients-dash/` - View all patients
- `appointments-dash/` - View all appointments

### **Reception Routes** (`/reception/`)
- `dashboard/` - Today's appointments
- `reception-signup/` - Register reception staff
- `create-appointment/<patient_id>/` - New appointment
- `update-status/<appointment_id>/` - Change appointment status

---

## 🛡️ Security Features

✅ **Account Lockout**: 15 failed attempts → 15-minute lockout  
✅ **Role-Based Access Control**: Decorators enforce permissions  
✅ **CSRF Protection**: Token validation on forms  
✅ **Phone Validation**: Validates Egyptian phone numbers  
✅ **Multi-Tenant Isolation**: Separate schemas per clinic  
✅ **Session Security**: Redis-backed secure sessions  
✅ **Input Validation**: Form validation and sanitization  

---

## Next Steps for Production Auth

- Configure `DEBUG=False`, set `ALLOWED_HOSTS` to all tenant/public domains, and add `CSRF_TRUSTED_ORIGINS` for those hosts.
- Enforce HTTPS: set `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`, `SESSION_COOKIE_SAMESITE='Lax'`, `SECURE_HSTS_SECONDS`, and `SECURE_PROXY_SSL_HEADER` if behind a proxy.
- Use a shared, fast session backend (e.g., Redis `cached_db`), and set `SESSION_COOKIE_DOMAIN` to cover tenant subdomains.
- Disable `debug_toolbar` in production (remove from `TENANT_APPS`/`MIDDLEWARE` or gate on `DEBUG`).
- Make logout tenant-aware: run `logout` inside the current tenant schema and redirect to the tenant domain for both staff and patients.
- Keep lockout in place and add IP/client throttling (e.g., django-ratelimit) on login endpoints; consider CAPTCHA for the passwordless patient login.
- Ensure patient login normalizes phone/username and audit that only the patient role can authenticate via the passwordless backend.
- Use HTTPS links in redirects (replace `http://...:8001` with the production host/port).

---

## 🗄️ Database Schema (PostgreSQL)

**Multi-tenant setup** using django-tenants:
- **Public schema**: Contains tenant definitions and routing
- **Tenant schemas**: Isolated data per clinic clinic

**Key Tables**:
- `doctor_user` - User accounts
- `doctor_doctor` - Doctor/staff information
- `patient_patient` - Patient records
- `patient_appointment` - Appointment scheduling
- `patient_diagnosis` - Medical diagnoses
- `patient_prescription` - Medication prescriptions
- `patient_requires` - Medical requirements

---

## 🔧 Configuration

### **Environment Variables** (`.env`)
```
DB_USER=postgres
DB_PASSWORD=<password>
DB_NAME=clinic_db
REDIS_URL=redis://redis:6379/0
DEBUG=False
SECRET_KEY=<django-secret>
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## 📚 Additional Resources

- **Django Documentation**: https://docs.djangoproject.com/
- **django-tenants**: https://django-tenants.readthedocs.io/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **Redis**: https://redis.io/docs/

---

## 📄 License

[Add your license here]

---

## 👥 Contributors

[Add contributors information]

---

**Last Updated**: December 2025
