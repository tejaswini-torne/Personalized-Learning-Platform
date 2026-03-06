# 🎓 Personalized Learning Platform

A **Personalized Learning Platform** that enables teachers to create assessments and manage classrooms while allowing students to participate in tests, access learning materials, and submit doubts.
The platform provides **role-based dashboards for teachers and students**, making learning more structured and interactive.

---

# 🚀 Features

### 👩‍🏫 Teacher Features

* Create and manage classrooms
* Create and publish MCQ tests
* Add questions and answer options
* Upload study notes and materials
* View student responses and progress
* Manage student doubts

### 👨‍🎓 Student Features

* Join classrooms using classroom codes
* Attempt online assessments
* View available tests
* Access study materials shared by teachers
* Submit doubts or questions
* Track learning activities

---

# 🛠️ Tech Stack

**Backend**

* Python
* Flask
* SQLAlchemy ORM

**Database**

* PostgreSQL

**Frontend**

* HTML
* CSS
* Bootstrap
* JavaScript

**Other Tools**

* Werkzeug (Password Hashing)
* Python Dotenv
* Git & GitHub

---

# 🧠 System Architecture

The platform follows a **Flask MVC-style architecture**:

* **Models** → Database tables using SQLAlchemy
* **Routes** → Backend logic and API endpoints
* **Templates** → HTML pages rendered using Jinja
* **Static Files** → CSS, JS, images, and uploaded files

---


# 🔐 Authentication

The platform uses **secure password hashing** with Werkzeug.

Features include:

* Secure login system
* Role-based access (Teacher / Student)
* Session management for user authentication

---

# 📊 Database Design

The platform includes multiple relational tables such as:

* Users
* Classrooms
* Tests
* Questions
* Options
* Student Answers
* Notes
* Doubts

These tables are connected using **foreign key relationships** to ensure proper data management.

---

# 🖥️ Screenshots

### 🏠 Landing Page



---

### 👨‍🎓 Student Dashboard



---

### 🏫 Student Classroom



---

### 👩‍🏫 Teacher Dashboard



---

### 📚 Teacher Classroom Management



---


# 🌱 Future Improvements

* AI-based learning recommendations
* Automatic grading system
* Student performance analytics
* Notification system
* Improved UI/UX
