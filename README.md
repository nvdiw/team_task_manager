# Team Task Management System

A production-ready task management web application built with **Django** that enables teams to create projects, assign tasks, track progress, and collaborate through comments.

**Live Demo:** *(Coming soon)*  
**Author:** [nvdiw](https://github.com/nvdiw)

---

## 📋 Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Usage Guide](#usage-guide)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Screenshots](#screenshots)
- [Future Improvements](#future-improvements)
- [License](#license)

---

## ✨ Features

### Core Features
| Feature | Description |
|---------|-------------|
| **User Authentication** | Complete signup, login, logout system with profile management |
| **Project Management** | Create, view, edit, and delete projects with team members |
| **Task Management** | Create tasks with priority levels and status tracking |
| **Team Collaboration** | Add multiple members to projects and assign tasks |
| **Comment System** | Add and delete comments on tasks for discussions |
| **Search** | Search projects by title or description |
| **Task Status** | One-click status toggle (TODO → IN PROGRESS → DONE) |
| **Pending Tasks Counter** | Color-coded badges showing incomplete tasks |

### Advanced Features
| Feature | Description |
|---------|-------------|
| **Permission System** | Users only see projects they own or are members of |
| **REST API** | Full RESTful API endpoints for all models |
| **Pagination** | 6 projects per page, 5 tasks per page |
| **Responsive Design** | Works on desktop, tablet, and mobile |
| **Custom CSS** | Beautiful styling with Font Awesome icons |

---

## 🛠 Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.13+ | Programming language |
| **Django** | 6.0.3 | Web framework |
| **Django REST Framework** | 3.17.1 | REST API development |
| **SQLite3** | - | Database (development) |
| **HTML5** | - | Frontend structure |
| **CSS3** | - | Styling (custom, no Bootstrap) |
| **Font Awesome** | 6.5.1 | Icons |

---

## 📦 Installation

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.13 or higher** - [Download Python](https://www.python.org/downloads/)
- **pip** - Comes with Python
- **Git** (optional) - For cloning the repository

> **Note:** Django and other dependencies will be installed automatically via `requirements.txt`.

### Step-by-Step Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/nvdiw/task-manager.git
cd task-manager
```

#### 2. Create Virtual Environment
**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```
**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```
#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Apply Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```
#### 5. Create Admin User (Superuser)
```bash
python manage.py createsuperuser
```
#### 6. Run Development Server
bash```
python manage.py runserver
```
---

## ✅ Installation Complete

Open your browser and visit: **http://127.0.0.1:8000**

🎉 Congratulations! Your Task Manager is now running.