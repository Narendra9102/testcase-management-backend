# 📌 Backend – Test Case Management System (Django)

This project is a backend REST API built using **Django + Django REST Framework**.
It provides **secure authentication**, **role-based access control**, **project collaboration**, and **test case management**.

---

## 🚀 Tech Stack

* Python 3.12+
* Django
* Django REST Framework
* MySQL
* JWT Authentication

---

## 📂 Project Setup Instructions

### 1️. Clone the Repository

```bash
git clone <your-github-repo-url>
cd testcase_management
```

---

### 2️. Create & Activate Virtual Environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### Linux / Mac

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3️. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🗄️ Database Setup (MySQL)

### 4️. Create Database

```sql
CREATE DATABASE testcase_management_db;
```

---

### 5️. Update `settings.py`

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'testcase_management_db',
        'USER': 'root',
        'PASSWORD': 'your_mysql_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

---

### 6️. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 👑 Create Superuser (Django Admin)

Superuser is **only for Django Admin Panel**, not for API usage.

```bash
python manage.py createsuperuser
```

Example:

```
Email: admin@test.com
Password: ********
```

Admin panel:

```
http://127.0.0.1:8000/admin/
```

> ⚠️ **Important:**
> Django superuser ≠ Application Admin Role
> Superuser manages DB via admin panel only.

---

## 🧩 Seed Roles (IMPORTANT)

```bash
python manage.py shell
```

```python
from accounts.models import Role

Role.objects.get_or_create(id=1, name="Admin", description="Full system access")
Role.objects.get_or_create(id=2, name="Organization", description="Can create and manage projects and testcases")
Role.objects.get_or_create(id=3, name="Member", description="Can work on assigned projects and testcases")

```

---

## 🔐 Authentication APIs

### ✅ Register User

**POST** `/api/auth/register/`

```json
{
  "name": "Narendra Sompalli",
  "email": "narendra@test.com",
  "password": "Password123",
  "phone": "+919849352538",
  "country": "India",
  "role_id": 2
}
```

---

### ✅ Login

**POST** `/api/auth/login/`

```json
{
  "email": "narendra@test.com",
  "password": "Password123"
}
```

Response includes **access token** and **refresh token**.

---

### ✅ Forgot Password

**POST** `/api/auth/forgot-password/`

```json
{
  "email": "narendra@test.com"
}
```

---

### ✅ Reset Password

**POST** `/api/auth/reset-password/`

```json
{
  "token": "reset-token",
  "new_password": "NewPassword@123"
}
```

---

## 🔑 JWT Authentication Usage

Include access token in headers:

```
Authorization: Bearer <access_token>
```

* Access token expires in short time
* Refresh token is used to generate a new access token

---

## 🧠 Role-Based System (Core Design)

### 🔹 Role 1 – Admin

* Django superuser only (manages database via admin panel)
* NOT used for API registration
* Created via: python manage.py createsuperuser

### 🔹 Role 2 – Organization

* Can create/update **their own projects**
* Can create/update **testcases under their projects**
* Can invite members to their projects

### 🔹 Role 3 – Member

* Cannot create projects
* Can create/update testcases **only in invited projects**
* Access depends on invitation status

---

## 📁 Project Workflow

### ✅ Create Project (Admin / Organization)

**POST** `/api/projects/`

```json
{
  "name": "Website Automation",
  "description": "E2E testcases for website"
}
```

---

## 👥 Invite Member to Project

**POST** `/api/projects/invite/`

```json
{
  "project": 2,
  "email": "tester@test.com",
  "role_in_project": "Tester"
}
```

Roles inside project:

* `Tester` → can create & update testcases
* `Contributor` → can create, update & delete testcases

---

## ✉️ Accept Invitation (Member)

**POST** `/api/projects/invitations/accept/`

```json
{
  "invitation_id": 1
}
```

Only after **Accepted** status → access is granted.

---

## 🧪 Test Case Management

### ✅ Create Test Case

**POST** `/api/testcases/`

```json
{
  "title": "Login Test",
  "description": "Verify login functionality",
  "steps": "Enter email, Enter password, Click login",
  "expected_result": "User should login successfully",
  "priority": "High",
  "project": 2
}
```

✔ Organization → must own the project
✔ Member → must be invited & accepted

---

### ✅ Get Testcases

**GET** `/api/testcases/?project_id=2`

Members only see testcases of projects they are invited to.

---

### ✅ Update Testcase

**PUT** `/api/testcases/{id}/`

```json
{
  "priority": "Medium"
}
```

---

### ✅ Delete Testcase

Only **Contributor** role can delete testcases.

---

## 🔐 Security & Validation Rules

* Backend strictly validates **role + membership**
* Invalid access always returns **403 Forbidden**
* Frontend bypass is impossible
* Soft delete used for safety

