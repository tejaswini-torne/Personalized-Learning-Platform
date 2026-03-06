from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import os, random, string
from models import db, McqTest, McqQuestion, McqOption, StudentAnswer


from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session



# ------------------------------------------------------
# Load environment variables
# ------------------------------------------------------
load_dotenv()


# ------------------------------------------------------
# Flask Configuration
# ------------------------------------------------------
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


# ------------------------------------------------------
# Initialize Flask app and Database
# ------------------------------------------------------
app = Flask(__name__)
app.config.from_object(Config)

# ✅ Only this one — do NOT call SQLAlchemy(app) again
db.init_app(app)

from models import McqTest, McqQuestion, McqOption, StudentAnswer, StudentDoubt



# ------------------------------------------------------
# Disable browser caching (your existing logic)
# ------------------------------------------------------
@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# -----------------------
# Database Models
# -----------------------
class User(db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # student / teacher

    classrooms = db.relationship('Classroom', backref='teacher', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Classroom(db.Model):
    __tablename__ = "classrooms"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(100))  # optional
    section = db.Column(db.String(50))   # optional

    tests = db.relationship("McqTest", backref="classroom", lazy=True)



# Mapping students to classrooms
class StudentClassroom(db.Model):
    __tablename__ = "student_classrooms"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=False)

    student = db.relationship("User", backref="joined_classrooms")
    classroom = db.relationship("Classroom", backref="students")

class TeacherNote(db.Model):
    __tablename__ = "teacher_notes"

    id = db.Column(db.Integer, primary_key=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    filepath = db.Column(db.String(300), nullable=False)











# -----------------------
# Routes
# -----------------------
@app.route("/")
def landing():
    # Correctly renders landing.html
    return render_template("landing.html")


@app.route("/get-started")
def get_started():
    if "user_id" not in session:
        flash("Please login first.", "danger")
        return redirect(url_for("login"))
    return render_template("get_started.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session["user_id"] = user.id
            session["role"] = user.role

            # Role-based redirect
            if user.role == "teacher":
                return redirect(url_for("teacher_dashboard"))
            elif user.role == "student":
                return redirect(url_for("student_dashboard"))
        else:
            flash("Invalid email or password", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please login.", "danger")
            return redirect(url_for("login"))

        new_user = User(username=username, email=email, role=role)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("registration.html")




# -----------------------
# Teacher Routes
# -----------------------
@app.route("/teacher/dashboard")
def teacher_dashboard():
    if "user_id" not in session or session.get("role") != "teacher":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    teacher_id = session["user_id"]
    classrooms = Classroom.query.filter_by(teacher_id=teacher_id).all()
    resp = make_response(render_template("teacher_dashboard.html", classrooms=classrooms))
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp



# @app.route("/teacher/leave_classroom/<int:classroom_id>", methods=["POST"])
# def leave_classrooms(classroom_id):
#     if "user_id" not in session or session.get("role") != "teacher":
#         flash("Access denied!", "danger")
#         return redirect(url_for("login"))

#     tc = TeacherClassroom.query.filter_by(
#         teacher_id=session["user_id"],
#         classroom_id=classroom_id
#     ).first()

#     if not tc:
#         flash("You are not part of this classroom.", "warning")
#         return redirect(url_for("teacher_dashboard"))

#     db.session.delete(tc)
#     db.session.commit()

#     flash("You have left the classroom.", "success")
#     return redirect(url_for("teacher_dashboard"))



@app.route("/create_classroom", methods=["GET", "POST"])
def create_classroom():
    if "user_id" not in session or session.get("role") != "teacher":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get("name")
        subject = request.form.get("subject")
        section = request.form.get("section")

        # Generate unique classroom code
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        while Classroom.query.filter_by(code=code).first():
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        new_classroom = Classroom(
            name=name,
            subject=subject,
            section=section,
            code=code,
            teacher_id=session["user_id"]
        )
        db.session.add(new_classroom)
        db.session.commit()

        flash("Classroom created successfully!", "success")
        return redirect(url_for("teacher_dashboard"))

    return render_template("create_classroom.html")

# # Teacher classrrom feature

# @app.route("/teacher/classroom/<int:classroom_id>")
# def teacher_classroom_features(classroom_id):
#     if "user_id" not in session or session.get("role") != "teacher":
#         flash("Access denied!", "danger")
#         return redirect(url_for("login"))

#     classroom = Classroom.query.get_or_404(classroom_id)

#     # Count students in that classroom
#     student_count = StudentClassroom.query.filter_by(classroom_id=classroom.id).count()

#     # ✅ Pass individual variables that your HTML expects
#     return render_template(
#         "teacher_classroom_features.html",
#         classroom_id=classroom.id,
#         classroom_name=classroom.name,
#         classroom_code=classroom.code,
#         student_count=student_count
#     )

@app.route("/teacher/classroom/<int:classroom_id>")
def teacher_classroom_features(classroom_id):
    if "user_id" not in session or session.get("role") != "teacher":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    classroom = Classroom.query.get_or_404(classroom_id)

    # Count students
    student_count = StudentClassroom.query.filter_by(classroom_id=classroom.id).count()

    # List of students
    enrolled_students = [
        sc.student for sc in StudentClassroom.query.filter_by(classroom_id=classroom.id).all()
    ]

    return render_template(
        "teacher_classroom_features.html",
        classroom_id=classroom.id,
        classroom_name=classroom.name,
        classroom_code=classroom.code,
        student_count=student_count,
        enrolled_students=enrolled_students
    )


@app.route("/teacher/mcq_test/<int:classroom_id>")
def teacher_mcq_test(classroom_id):
    if "user_id" not in session or session.get("role") != "teacher":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))
    return render_template("teacher_mcq_test.html", classroom_id=classroom_id)

from flask import request, jsonify
from models import db, McqTest, McqQuestion, McqOption

@app.route("/save_test", methods=["POST"])
def save_test():
    data = request.get_json()
    title = data.get("name")  # your HTML form sends it as 'name'
    description = data.get("description")
    questions = data.get("questions", [])
    classroom_id = data.get("classroom_id")  # ✅ Added
    teacher_id = session.get("user_id")
 # (Replace later with session.get("user_id"))

    if not title or not questions:
        return jsonify({"error": "Missing test title or questions"}), 400

    try:
        # ✅ Include classroom_id
        test = McqTest(
            title=title,
            description=description,
            teacher_id=teacher_id,
            classroom_id=classroom_id
        )
        db.session.add(test)
        db.session.flush()

        for q in questions:
            question_text = q.get("question")
            q_type = q.get("type", "mcq")
            correct_option = q.get("correct") if q_type == "mcq" else None

            question = McqQuestion(
                test_id=test.id,
                question_text=question_text,
                question_type=q_type,
                correct_option=str(correct_option) if correct_option else None,
            )
            db.session.add(question)
            db.session.flush()

            
            if q_type == "mcq":
                options_list = []

                for idx, opt_text in enumerate(q.get("options", []), start=1):
                    opt = McqOption(
                    question_id=question.id,
                    option_text=opt_text
                    )
                    db.session.add(opt)
                    db.session.flush()   # get opt.id
                    options_list.append(opt)
                
         # Now assign correct option based on index selected by teacher
                correct_index = int(q.get("correct"))  # e.g., 1,2,3,4
                question.correct_option = str(options_list[correct_index - 1].id)




            elif q_type == "text":
                # store correct textual answer as correct_option if available
                answer = q.get("answer")
                if answer:
                    question.correct_option = answer

        db.session.commit()
        return jsonify({"message": "✅ Test saved successfully"}), 200

    except Exception as e:
        db.session.rollback()
        print("❌ Error saving test:", e)
        return jsonify({"error": "Failed to save test"}), 500
    

    


@app.route("/teacher/doubt_session/<int:classroom_id>")
def teacher_doubt_session(classroom_id):
    if "user_id" not in session or session.get("role") != "teacher":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))
    return render_template("teacher_doubt_session.html", classroom_id=classroom_id)











# -----------------------
# Teacher Classroom Feature Subpages
# -----------------------



import os
import uuid
from flask import request, render_template, flash, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename
# from your_app import app, db
# from your_app.models import TeacherNote, Classroom

# -----------------------------
# TEACHER NOTES FOLDER (separate from student doubts)
# -----------------------------
# Use an absolute path outside OneDrive if possible for reliability
import os
import uuid
from flask import request, render_template, flash, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename

# -----------------------------
# TEACHER NOTES FOLDER
# -----------------------------
TEACHER_NOTES_FOLDER = os.path.join(os.getcwd(), "notes_folder")
os.makedirs(TEACHER_NOTES_FOLDER, exist_ok=True)
print("Teacher Notes folder:", TEACHER_NOTES_FOLDER)

# -----------------------------
# ALLOWED FILES (allow all)
# -----------------------------
def allowed_note_file(filename):
    return bool(filename) and "." in filename


# -----------------------------
# TEACHER — Upload + List Notes
# -----------------------------
@app.route("/teacher/notes/<int:classroom_id>", methods=["GET", "POST"])
def teacher_notes(classroom_id):
    if "user_id" not in session or session.get("role") != "teacher":
        flash("Access denied!", "danger")
        print("DEBUG: Access denied, not a teacher or not logged in")
        return redirect(url_for("login"))

    classroom = Classroom.query.get_or_404(classroom_id)
    notes = TeacherNote.query.filter_by(classroom_id=classroom_id).all()

    if request.method == "POST":
        title = request.form.get("title")
        file = request.files.get("file")

        # Debug prints
        print("DEBUG: POST request received")
        print("Uploading to TEACHER_NOTES_FOLDER:", TEACHER_NOTES_FOLDER)
        print("Current working directory:", os.getcwd())
        print("Folder exists?", os.path.exists(TEACHER_NOTES_FOLDER))
        print("Received file object:", file)
        print("Received filename:", file.filename if file else None)

        if not title:
            print("DEBUG: Title missing")
            flash("Title is required!", "danger")
            return redirect(request.url)

        if not file or file.filename == "":
            print("DEBUG: No file received!")
            flash("Please select a file!", "danger")
            return redirect(request.url)

        if allowed_note_file(file.filename):

            # Sanitize filename and generate unique name
            original = secure_filename(file.filename)
            ext = original.rsplit(".", 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(TEACHER_NOTES_FOLDER, filename)

            try:
                file.save(filepath)
                print("DEBUG: file.save() completed")
                print("DEBUG: Does file exist now?", os.path.exists(filepath))
            except Exception as e:
                print("DEBUG: Error saving file:", e)
                flash("Error saving file! Check folder permissions.", "danger")
                return redirect(request.url)

            # Save note to database
            note = TeacherNote(
                classroom_id=classroom_id,
                title=title,
                filename=filename,
                filepath=filepath
            )
            db.session.add(note)
            db.session.commit()
            print(f"DEBUG: Note saved in database with filename {filename}")

            flash("Note uploaded successfully!", "success")
            return redirect(url_for("teacher_notes", classroom_id=classroom_id))
        else:
            print("DEBUG: File type not allowed:", file.filename)
            flash("File type not allowed!", "danger")
            return redirect(request.url)

    print("DEBUG: Rendering GET template")
    return render_template("teacher_notes.html", classroom=classroom, notes=notes)



# -----------------------------
# TEACHER — View Note
# -----------------------------
@app.route("/teacher/notes/view/<path:filename>")
def view_teacher_note(filename):
    if "user_id" not in session or session.get("role") != "teacher":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    try:
        # Open in browser (NOT download)
        return send_from_directory(
            TEACHER_NOTES_FOLDER,
            filename,
            as_attachment=False
        )
    except FileNotFoundError:
        flash("File not found!", "danger")
        return redirect(request.referrer or url_for("teacher_notes"))

# -----------------------------
# TEACHER — Delete Note
# -----------------------------
@app.route("/teacher/notes/delete/<int:note_id>/<int:classroom_id>", methods=["POST"])
def delete_teacher_note(note_id, classroom_id):
    if "user_id" not in session or session.get("role") != "teacher":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    note = TeacherNote.query.get_or_404(note_id)

    # Delete actual file from notes_folder
    if os.path.exists(note.filepath):
        try:
            os.remove(note.filepath)
            print("Deleted file:", note.filepath)
        except Exception as e:
            print("Error deleting file:", e)
            flash("Error deleting file from folder!", "danger")

    db.session.delete(note)
    db.session.commit()

    flash("Note deleted successfully!", "success")
    return redirect(url_for("teacher_notes", classroom_id=classroom_id))





@app.route("/teacher/classroom/<int:classroom_id>/create-mcq-test")
def create_mcq_test(classroom_id):
    # ✅ Authentication check
    if "user_id" not in session or session.get("role") != "teacher":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))
    
    # ✅ Fetch classroom safely
    classroom = Classroom.query.get_or_404(classroom_id)

    # ✅ Pass classroom to the template
    return render_template(
        "create_mcq_test.html",
        classroom=classroom,
        classroom_id=classroom_id
    )

@app.route("/teacher/test/<int:test_id>/view")
def view_test(test_id):
    if "user_id" not in session or session.get("role") != "teacher":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    test = McqTest.query.get_or_404(test_id)

    # Ensure teacher has permission
    if test.teacher_id != session.get("user_id"):
        flash("Unauthorized access!", "danger")
        return redirect(url_for("teacher_dashboard"))

    return render_template("view_single_test.html", test=test, user_role="teacher")



@app.route("/teacher/test/<int:test_id>/post")
def post_test(test_id):
    if "user_id" not in session or session.get("role") != "teacher":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    test = McqTest.query.get_or_404(test_id)
    
    # Mark the test as posted
    test.is_posted = True
    db.session.commit()

    flash("Test has been posted successfully!", "success")
    return redirect(request.referrer or url_for("teacher_dashboard"))



@app.route('/teacher/delete_test/<int:test_id>', methods=['POST'])
def delete_test(test_id):
    test = McqTest.query.get_or_404(test_id)

    try:
        # 1️⃣ Delete all student answers for this test
        StudentAnswer.query.filter(
            StudentAnswer.question_id.in_(
                db.session.query(McqQuestion.id).filter_by(test_id=test_id)
            )
        ).delete(synchronize_session=False)

        # 2️⃣ Delete all options for questions
        McqOption.query.filter(
            McqOption.question_id.in_(
                db.session.query(McqQuestion.id).filter_by(test_id=test_id)
            )
        ).delete(synchronize_session=False)

        # 3️⃣ Delete all questions
        McqQuestion.query.filter_by(test_id=test_id).delete()

        # 4️⃣ Delete the test itself
        db.session.delete(test)
        db.session.commit()

        return jsonify({"message": "Deleted"}), 200

    except Exception as e:
        db.session.rollback()
        print("Error deleting test:", e)
        return jsonify({"error": "Failed to delete test"}), 500


@app.route("/teacher/test/<int:test_id>/edit")
def edit_test(test_id):
    if "user_id" not in session or session.get("role") != "teacher":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    test = McqTest.query.get_or_404(test_id)

    if test.teacher_id != session.get("user_id"):
        flash("Unauthorized access!", "danger")
        return redirect(url_for("teacher_dashboard"))

    return render_template("edit_test.html", test=test)


@app.route('/teacher/test/<int:test_id>/update', methods=['POST'])
def update_test(test_id):
    if "user_id" not in session or session.get("role") != "teacher":
        return jsonify({"error": "Access denied"}), 403

    test = McqTest.query.get_or_404(test_id)

    # Verify that the teacher owns this test
    if test.teacher_id != session.get("user_id"):
        return jsonify({"error": "Unauthorized access"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    title = data.get("title")
    description = data.get("description")
    questions = data.get("questions")

    if not title or not description or not isinstance(questions, list):
        return jsonify({"error": "Missing or invalid fields"}), 400

    try:
        test.title = title
        test.description = description

        # Remove old questions and their options
        old_questions = McqQuestion.query.filter_by(test_id=test_id).all()
        for q in old_questions:
            McqOption.query.filter_by(question_id=q.id).delete()
        McqQuestion.query.filter_by(test_id=test_id).delete()

        # Insert new questions and options
        for q in questions:
            q_type = q.get("type")
            question_text = q.get("question")
            if not question_text or not q_type:
                continue  # Skip invalid questions

            correct_answer = q.get("correct") if q_type == "mcq" else q.get("answer")

            new_q = McqQuestion(
                test_id=test_id,
                question_text=question_text,
                question_type=q_type,
                correct_option=correct_answer
            )
            db.session.add(new_q)
            db.session.flush()  # Get new_q.id

            # Add options if MCQ
            if q_type == "mcq":
                options = q.get("options", [])
                for opt in options:
                    if opt:  # Skip empty options
                        db.session.add(McqOption(
                            question_id=new_q.id,
                            option_text=opt
                        ))

        db.session.commit()
        return jsonify({"success": True})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500






@app.route("/teacher/classroom/<int:classroom_id>/query-test")
def teacher_query_test(classroom_id):
    # Check access permissions
    if "user_id" not in session or session.get("role") != "teacher":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    classroom = Classroom.query.get_or_404(classroom_id)
    teacher_id = session.get("user_id")

    tests = (
        McqTest.query
        .filter_by(classroom_id=classroom.id, teacher_id=teacher_id)
        .order_by(McqTest.created_at.desc())
        .all()
    )

    return render_template("view_test_and_records.html", classroom=classroom, tests=tests)







# -----------------------------------
# Teacher Doubt Session
# -----------------------------------

@app.route("/teacher/classroom/<int:classroom_id>/doubt-session")
def doubt_session(classroom_id):
    if "user_id" not in session or session.get("role") != "teacher":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    classroom = Classroom.query.get_or_404(classroom_id)

    # Fetch doubts in latest-first order
    doubts = StudentDoubt.query.filter_by(classroom_id=classroom_id) \
                               .order_by(StudentDoubt.date_created.desc()).all()

    doubts_with_names = []
    for d in doubts:
        student = User.query.get(d.student_id)

        doubts_with_names.append({
            "id": d.id,
    "student_name": student.username if student else "Unknown",
            "description": d.description,
            "image_filename": d.image_filename,
            "date_created": d.date_created,
            "status": d.status if d.status else "Pending",
            "reply": d.reply if d.reply else ""
        })

    return render_template("teacher_doubt.html", classroom=classroom, doubts=doubts_with_names)

@app.route("/teacher/classroom/<int:classroom_id>/post_announcement", methods=["POST"])
def post_announcement(classroom_id):
    if "user_id" not in session or session.get("role") != "teacher":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    announcement_text = request.form.get("announcement")

    if not announcement_text:
        flash("Announcement cannot be empty!", "warning")
        return redirect(url_for("doubt_session", classroom_id=classroom_id))

    # Later save announcements into a table
    flash("Announcement posted successfully!", "success")
    return redirect(url_for("doubt_session", classroom_id=classroom_id))


@app.route("/teacher/doubt/<int:doubt_id>/reply", methods=["POST"])
def reply_student_doubt(doubt_id):
    if "user_id" not in session or session.get("role") != "teacher":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    doubt = StudentDoubt.query.get_or_404(doubt_id)
    doubt.reply = request.form.get("reply")
    doubt.status = "Answered"

    db.session.commit()

    flash(f"Replied to doubt #{doubt.id} successfully!", "success")
    return redirect(url_for("doubt_session", classroom_id=doubt.classroom_id))


@app.route("/teacher/doubt/<int:doubt_id>/resolve", methods=["POST"])
def resolve_student_doubt(doubt_id):
    if "user_id" not in session or session.get("role") != "teacher":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    doubt = StudentDoubt.query.get_or_404(doubt_id)
    doubt.status = "Resolved"

    db.session.commit()

    flash("Doubt marked as resolved!", "success")
    return redirect(url_for("doubt_session", classroom_id=doubt.classroom_id))


@app.route("/teacher/doubt/<int:doubt_id>/delete", methods=["POST"])
def delete_student_doubt_teacher(doubt_id):
    if "user_id" not in session or session.get("role") != "teacher":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    doubt = StudentDoubt.query.get_or_404(doubt_id)

    # Delete uploaded file if exists
    if doubt.image_filename:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], doubt.image_filename))
        except:
            pass

    classroom_id = doubt.classroom_id

    db.session.delete(doubt)
    db.session.commit()

    flash("Doubt deleted successfully!", "success")
    return redirect(url_for("doubt_session", classroom_id=classroom_id))



# ✅ Analysis
@app.route("/teacher/classroom/<int:classroom_id>/analysis")
def teacher_analysis(classroom_id):  # <--- changed function name
    if "user_id" not in session or session.get("role") != "teacher":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    classroom = Classroom.query.get_or_404(classroom_id)
    posted_tests = McqTest.query.filter_by(classroom_id=classroom_id, is_posted=True).all()


    return render_template("teacher_analysis.html", classroom=classroom, tests=posted_tests)


from sqlalchemy import func

from flask import render_template
from sqlalchemy import func

@app.route("/teacher/test/<int:test_id>/details")
def test_details(test_id):
    test = McqTest.query.get_or_404(test_id)

    # Total possible marks
    total_marks = sum(q.marks for q in test.questions)

    # Aggregate student marks
    students_marks = (
        db.session.query(
            StudentAnswer.student_id,
            func.sum(StudentAnswer.marks_obtained).label("total_obtained")
        )
        .filter(StudentAnswer.test_id == test_id)
        .group_by(StudentAnswer.student_id)
        .order_by(func.sum(StudentAnswer.marks_obtained).desc())
        .all()
    )

    student_data = []
    for s_id, marks in students_marks:
        student = User.query.get(s_id)
        student_data.append({
            "id": student.id,
            "name": student.username,
            "marks_obtained": marks
        })

    total_students = len(student_data)

    chart_labels = [s["name"] for s in student_data]
    chart_data = [s["marks_obtained"] for s in student_data]

    return render_template(
        "test_details.html",
        test=test,
        total_students=total_students,
        total_marks=total_marks,
        student_data=student_data,
        chart_labels=chart_labels,
        chart_data=chart_data
    )







# -----------------------
# Student Routesc
# -----------------------
@app.route("/student/dashboard")
def student_dashboard():
    if "user_id" not in session or session.get("role") != "student":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    student_id = session["user_id"]
    classrooms = StudentClassroom.query.filter_by(student_id=student_id).all()
    resp = make_response(render_template("student_dashboard.html", classrooms=classrooms))
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp



@app.route("/student/leave_classroom/<int:classroom_id>")
def leave_classroom(classroom_id):
    if "user_id" not in session or session.get("role") != "student":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    # Find the student-classroom record
    sc = StudentClassroom.query.filter_by(
        student_id=session["user_id"],
        classroom_id=classroom_id
    ).first()

    if not sc:
        flash("You are not part of this classroom.", "warning")
        return redirect(url_for("student_dashboard"))

    # Remove it
    db.session.delete(sc)
    db.session.commit()

    flash("You have left the classroom.", "success")
    return redirect(url_for("student_dashboard"))



@app.route("/join_classroom", methods=["GET", "POST"])
def join_classroom():
    if "user_id" not in session or session.get("role") != "student":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        code = request.form.get("code").strip().upper()
        classroom = Classroom.query.filter_by(code=code).first()
        if not classroom:
            flash("Invalid classroom code.", "danger")
        else:
            exists = StudentClassroom.query.filter_by(
                student_id=session["user_id"], classroom_id=classroom.id
            ).first()
            if exists:
                flash("You have already joined this classroom.", "info")
            else:
                join = StudentClassroom(student_id=session["user_id"], classroom_id=classroom.id)
                db.session.add(join)
                db.session.commit()
                flash(f"Joined classroom '{classroom.name}' successfully!", "success")
                return redirect(url_for("student_dashboard"))

    return render_template("join_classroom.html")



# -------------------
# Student Classroom Features
# -------------------
@app.route("/student/classroom/<int:classroom_id>")
def student_classroom_features(classroom_id):
    # Fetch classroom and relevant data
    classroom = Classroom.query.get_or_404(classroom_id)
    # Example: fetch tests in this classroom
    tests = McqTest.query.filter_by(classroom_id=classroom.id).all()
    return render_template("student/student_classroom_features.html", classroom=classroom, tests=tests)


# -------------------
# Notes
# -------------------
import os
from flask import render_template, session, flash, redirect, url_for, send_from_directory, abort

# (Keep your existing UPLOAD_FOLDER / app.config assignment)
# UPLOAD_FOLDER = os.path.join("static", "uploads", "notes")
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# If your teacher code uses a different folder var, keep it defined too.
# TEACHER_NOTES_FOLDER = os.path.join(os.getcwd(), "notes_folder")

# ----------------------------------------------------
# STUDENT NOTES LIST PAGE
# ----------------------------------------------------
@app.route("/student/notes/<int:classroom_id>")
def student_notes(classroom_id):
    if "user_id" not in session or session.get("role") != "student":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    classroom = Classroom.query.get_or_404(classroom_id)
    notes = TeacherNote.query.filter_by(classroom_id=classroom_id).all()

    return render_template(
        "student/student_notes.html",
        classroom=classroom,
        notes=notes
    )


# ----------------------------------------------------
# Helper: resolve actual folder and filename from DB record
# ----------------------------------------------------
def _resolve_note_file_paths(note):
    """
    Given a TeacherNote instance, return (directory, filename) to pass to send_from_directory.
    This function is conservative: it ensures no path traversal and checks both our configured
    upload folder and any absolute filepath stored in the DB (note.filepath).
    """
    # Preference: if note.filepath exists and file exists there, use its directory
    # Otherwise fall back to app.config["UPLOAD_FOLDER"]
    # Ensure filename is basename to prevent path traversal
    filename = os.path.basename(note.filename or "")

    # 1) If DB has an absolute filepath and file exists -> use its directory
    if getattr(note, "filepath", None):
        db_path = note.filepath
        if db_path:
            # Normalize and check
            db_path = os.path.abspath(db_path)
            if os.path.exists(db_path):
                return (os.path.dirname(db_path), os.path.basename(db_path))

    # 2) Next try configured folder
    folder = app.config.get("UPLOAD_FOLDER") or ""
    folder_abs = os.path.abspath(folder)
    file_path = os.path.join(folder_abs, filename)
    if os.path.exists(file_path):
        return (folder_abs, filename)

    # 3) Last resort: if teacher files are stored in TEACHER_NOTES_FOLDER (if defined)
    teacher_folder = globals().get("TEACHER_NOTES_FOLDER")
    if teacher_folder:
        teacher_abs = os.path.abspath(teacher_folder)
        file_path = os.path.join(teacher_abs, filename)
        if os.path.exists(file_path):
            return (teacher_abs, filename)

    # Not found -> return best-effort folder and filename (used by caller to abort)
    return (folder_abs, filename)


# ----------------------------------------------------
# VIEW NOTE (opens file in browser)
# ----------------------------------------------------
@app.route("/student/notes/view/<int:note_id>")
def view_note(note_id):
    if "user_id" not in session or session.get("role") != "student":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    note = TeacherNote.query.get_or_404(note_id)

    directory, filename = _resolve_note_file_paths(note)

    # Prevent empty filename or path traversal
    if not filename or filename in (".", ".."):
        return abort(404)

    file_path = os.path.join(directory, filename)
    if not os.path.exists(file_path):
        return abort(404)

    # Serve for inline viewing (browser will open if it can preview the type)
    return send_from_directory(directory=directory, path=filename, as_attachment=False)


# ----------------------------------------------------
# DOWNLOAD NOTE
# ----------------------------------------------------
@app.route("/student/notes/download/<int:note_id>")
def download_note(note_id):
    if "user_id" not in session or session.get("role") != "student":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    note = TeacherNote.query.get_or_404(note_id)

    directory, filename = _resolve_note_file_paths(note)

    if not filename or filename in (".", ".."):
        return abort(404)

    file_path = os.path.join(directory, filename)
    if not os.path.exists(file_path):
        return abort(404)

    return send_from_directory(directory=directory, path=filename, as_attachment=True)


# -------------------
# Student: View New Tests
# -------------------
@app.route("/student/<int:classroom_id>/new_tests")
def student_new_tests(classroom_id):

    student_id = session.get("user_id")

    if not student_id or session.get("role") != "student":
        flash("Please login as student.", "danger")
        return redirect(url_for("login"))

    tests = McqTest.query.filter_by(classroom_id=classroom_id, is_posted=True).all()


    test_list = []

    for t in tests:
        answers = StudentAnswer.query.filter_by(
            student_id=student_id,
            test_id=t.id
        ).all()

        if answers:
            status = "completed"

            # ⭐ Count correct answers (marks_obtained is 1 or 0)
            marks_obtained = sum(a.marks_obtained for a in answers)

            # ⭐ Total questions in test
            total_questions = McqQuestion.query.filter_by(test_id=t.id).count()

        else:
            status = "pending"
            marks_obtained = None
            total_questions = None

        test_list.append({
            "id": t.id,
            "title": t.title,
            "created_at": t.created_at.strftime("%Y-%m-%d"),
            "status": status,
            "marks": marks_obtained,
            "total": total_questions
        })

    return render_template(
        "student/student_test.html",
        tests=test_list,
        classroom_id=classroom_id
    )



@app.route("/student/start_test/<int:test_id>")
def start_test(test_id):

    # Check if student is logged in
    student_id = session.get("user_id")
    if not student_id or session.get("role") != "student":
        flash("Please login as student.", "danger")
        return redirect(url_for("login"))

    # Get the test
    test = McqTest.query.get_or_404(test_id)

    # Get all questions of this test
    questions = McqQuestion.query.filter_by(test_id=test_id).all()

    return render_template(
        "student/start_test.html",
        test=test,
        questions=questions
    )



@app.route("/student/submit_test/<int:test_id>", methods=["POST"])
def submit_test(test_id):

    student_id = session.get("user_id")

    if not student_id or session.get("role") != "student":
        flash("Please login as student.", "danger")
        return redirect(url_for("login"))

    test = McqTest.query.get(test_id)

    # Loop through answers submitted by the student
    for key, value in request.form.items():

        if key.startswith("question_"):
            question_id = int(key.split("_")[1])
            selected_option = value

            question = McqQuestion.query.get(question_id)

            # ⭐ Calculate marks correctly
            if question.question_type == "mcq":
                is_correct = (selected_option == question.correct_option)
                marks = question.marks if is_correct else 0

            else:  # text question
                is_correct = (selected_option.strip().lower() ==
                              question.correct_option.strip().lower())
                marks = question.marks if is_correct else 0

            # Save student's answer
            answer = StudentAnswer(
                student_id=student_id,
                test_id=test_id,
                question_id=question_id,
                selected_option=selected_option,
                marks_obtained=marks
            )

            db.session.add(answer)

    db.session.commit()

    flash("Test submitted successfully!", "success")

    return redirect(url_for("student_new_tests", classroom_id=test.classroom_id))



# -------------------
# Test & Records
# -------------------
@app.route("/student/test_and_records/<int:classroom_id>")
def student_test_and_records(classroom_id):
    # Ensure student is logged in
    if session.get("role") != "student" or not session.get("user_id"):
        flash("Please login as student.", "danger")
        return redirect(url_for("login"))

    student_id = session.get("user_id")

    # Get all tests in this classroom
    tests = McqTest.query.filter_by(classroom_id=classroom_id).all()
    completed_tests = []

    for test in tests:
        # Get all answers by this student for this test
        answers = StudentAnswer.query.filter_by(student_id=student_id, test_id=test.id).all()
        
        if not answers:
            continue  # student hasn't attempted this test

        # Total marks obtained by student
        total_marks = sum(a.marks_obtained for a in answers)

        # Total marks possible
        max_marks = sum(q.marks for q in test.questions)

        # Check if all questions attempted
        if len(answers) == len(test.questions):
            completed_tests.append({
                "id": test.id,
                "title": test.title,
                "created_at": test.created_at.strftime("%Y-%m-%d"),
                "status": "completed",
                "marks": f"{total_marks} / {max_marks}"
            })

    # Render the template from student subfolder
    return render_template(
        "student/test_and_records.html",  # ensure this file exists here
        tests=completed_tests,
        classroom_id=classroom_id
    )

# @app.route("/student/test_record_detail/<int:test_id>")
# def test_record_detail(test_id):
#     if session.get("role") != "student" or not session.get("user_id"):
#         flash("Please login as student.", "danger")
#         return redirect(url_for("login"))

#     student_id = session.get("user_id")
#     test = McqTest.query.get_or_404(test_id)

#     # Fetch all student answers for this test
#     student_answers = StudentAnswer.query.filter_by(student_id=student_id, test_id=test_id).all()
#     answers_dict = {a.question_id: a for a in student_answers}

#     questions_data = []
#     total_obtained = 0
#     total_marks = 0

#     for q in test.questions:
#         student_answer = answers_dict.get(q.id)
#         marks_obtained = student_answer.marks_obtained if student_answer else 0
#         total_obtained += marks_obtained
#         total_marks += q.marks

#         # Include all options text for the question
#         option_texts = [opt.option_text for opt in q.options]

#         questions_data.append({
#             "question_text": q.question_text,
#             "correct_option": q.correct_option,              # correct answer text
#             "student_answer": student_answer.selected_option if student_answer else None,  # student's selected option text
#             "marks_obtained": marks_obtained,
#             "total_marks": q.marks,
#             "options": option_texts
#         })

#     return render_template(
#         "student/test_record_detail.html",
#         test=test,
#         questions=questions_data,
#         total_obtained=total_obtained,
#         total_marks=total_marks
#     )

@app.route("/student/test_record_detail/<int:test_id>")
def test_record_detail(test_id):
    if session.get("role") != "student" or not session.get("user_id"):
        flash("Please login as student.", "danger")
        return redirect(url_for("login"))

    student_id = session.get("user_id")
    test = McqTest.query.get_or_404(test_id)

    # Fetch all student answers for this test
    student_answers = StudentAnswer.query.filter_by(student_id=student_id, test_id=test_id).all()
    answers_dict = {a.question_id: a for a in student_answers}

    questions_data = []
    total_obtained = 0
    total_marks = 0

    for q in test.questions:
        student_answer_obj = answers_dict.get(q.id)
        marks_obtained = student_answer_obj.marks_obtained if student_answer_obj else 0
        total_obtained += marks_obtained
        total_marks += q.marks

        # List of option texts
        option_texts = [opt.option_text for opt in q.options]

        # Determine correct option text
        correct_option_text = None
        if q.correct_option:
            try:
                opt_id = int(q.correct_option)  # If stored as option ID
                correct_opt = McqOption.query.get(opt_id)
                if correct_opt:
                    correct_option_text = correct_opt.option_text
            except ValueError:
                correct_option_text = q.correct_option  # Otherwise text

        # Determine student selected option text
        student_selected_text = None
        if student_answer_obj:
            sel = student_answer_obj.selected_option
            if sel:
                try:
                    idx = int(sel) - 1  # convert 1-based index to 0-based
                    if 0 <= idx < len(option_texts):
                        student_selected_text = option_texts[idx]
                    else:
                        student_selected_text = sel  # fallback if out of bounds
                except ValueError:
                    # If stored as text
                    # Try to match with an option text (for wrong answers)
                    if sel in option_texts:
                        student_selected_text = sel
                    else:
                        student_selected_text = sel  # wrong choice not in options

        questions_data.append({
            "question_text": q.question_text,
            "correct_option": correct_option_text,
            "student_answer": student_selected_text,
            "marks_obtained": marks_obtained,
            "total_marks": q.marks,
            "options": option_texts
        })

    return render_template(
        "student/test_record_detail.html",
        test=test,
        questions=questions_data,
        total_obtained=total_obtained,
        total_marks=total_marks
    )




from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from werkzeug.utils import secure_filename
from models import db, StudentDoubt

UPLOAD_FOLDER = 'static/uploads/doubts'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# -------------------------------------------
# Helper Function
# -------------------------------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



# -------------------------------------------
# STUDENT DOUBT SESSION PAGE
# -------------------------------------------
@app.route("/student/<int:classroom_id>/doubt_session")
def student_doubt_session(classroom_id):
    if "user_id" not in session or session.get("role") != "student":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    student_id = session.get("user_id")

    doubts = StudentDoubt.query.filter_by(
        student_id=student_id,
        classroom_id=classroom_id
    ).order_by(StudentDoubt.date_created.desc()).all()

    return render_template(
        "student/student_doubt.html",
        doubts=doubts,
        classroom_id=classroom_id
    )



# -------------------------------------------
# SUBMIT DOUBT
# -------------------------------------------
@app.route("/student/<int:classroom_id>/doubt_session/submit", methods=["POST"])
def submit_student_doubt(classroom_id):
    if "user_id" not in session or session.get("role") != "student":
        flash("Access denied!", "danger")
        return redirect(url_for("login"))

    desc = request.form.get("doubtDesc")
    image = request.files.get("doubtImage")

    filename = None
    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    new_doubt = StudentDoubt(
        student_id=session["user_id"],
        classroom_id=classroom_id,
        description=desc,
        image_filename=filename
    )

    db.session.add(new_doubt)
    db.session.commit()

    flash("Doubt submitted successfully!", "success")
    return redirect(url_for("student_doubt_session", classroom_id=classroom_id))



# -------------------------------------------
# DELETE DOUBT
# -------------------------------------------
@app.route("/student/<int:classroom_id>/doubt_session/delete/<int:doubt_id>", methods=["POST"])
def delete_student_doubt(classroom_id, doubt_id):
    doubt = StudentDoubt.query.get_or_404(doubt_id)

    if doubt.student_id != session.get("user_id"):
        flash("Unauthorized action!", "danger")
        return redirect(url_for("student_doubt_session", classroom_id=classroom_id))

    # Delete associated image file
    if doubt.image_filename:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], doubt.image_filename))
        except:
            pass

    db.session.delete(doubt)
    db.session.commit()

    flash("Doubt deleted successfully!", "success")
    return redirect(url_for("student_doubt_session", classroom_id=classroom_id))



# -------------------
# Helper: ordinal suffix
# -------------------
def ordinal_suffix(n: int) -> str:
    """Return ordinal suffix for an integer (1 -> 'st', 2 -> 'nd', 3 -> 'rd', else 'th')."""
    if 10 <= (n % 100) <= 20:
        return "th"
    if n % 10 == 1:
        return "st"
    if n % 10 == 2:
        return "nd"
    if n % 10 == 3:
        return "rd"
    return "th"


# -------------------
# Calculate overall rank for all students in a classroom
# -------------------
def calculate_all_ranks(classroom_id):
    """
    Calculate overall percentage and rank for all students in a classroom.
    Returns: { student_id: (rank, percentage), ... }
    """
    tests = McqTest.query.filter_by(classroom_id=classroom_id).all()
    student_percentages = {}

    for student in User.query.filter_by(role="student").all():
        total_scored = 0
        total_max = 0
        for test in tests:
            answers = StudentAnswer.query.filter_by(student_id=student.id, test_id=test.id).all()
            if not answers:
                continue
            obtained = sum(a.marks_obtained for a in answers)
            max_marks = sum(q.marks for q in test.questions)
            total_scored += obtained
            total_max += max_marks
        percentage = (total_scored / total_max) * 100 if total_max > 0 else 0
        student_percentages[student.id] = percentage

    sorted_percentages = sorted(student_percentages.values(), reverse=True)
    ranks = {}
    for sid, perc in student_percentages.items():
        rank = sorted_percentages.index(perc) + 1
        ranks[sid] = (rank, round(perc, 2))

    return ranks


# -------------------
# Student Analysis Route
# -------------------
@app.route("/student/<int:classroom_id>/analysis")
def student_analysis(classroom_id):
    if session.get("role") != "student" or not session.get("user_id"):
        flash("Please login as student.", "danger")
        return redirect(url_for("login"))

    student_id = session.get("user_id")
    classroom = Classroom.query.get_or_404(classroom_id)
    student = User.query.get(student_id)

    tests = McqTest.query.filter_by(classroom_id=classroom_id).all()
    test_records = []
    percentages = []
    best_score = 0
    best_test_name = ""

    # --- get overall ranks for all students ---
    all_ranks = calculate_all_ranks(classroom_id)
    student_rank, _ = all_ranks.get(student_id, ("-", 0))
    rank_suffix = ordinal_suffix(student_rank) if student_rank != "-" else ""

    for test in tests:
        answers = StudentAnswer.query.filter_by(student_id=student_id, test_id=test.id).all()
        if not answers:
            continue

        obtained = sum(a.marks_obtained for a in answers)
        max_marks = sum(q.marks for q in test.questions)
        if max_marks == 0:
            continue

        percentage = round((obtained / max_marks) * 100, 2)
        percentages.append(percentage)

        if percentage > best_score:
            best_score = percentage
            best_test_name = test.title

        # --- per-test rank among all students ---
        all_answers = StudentAnswer.query.filter_by(test_id=test.id).all()
        test_student_percentages = {}
        for a in all_answers:
            test_student_percentages.setdefault(a.student_id, 0)
            test_student_percentages[a.student_id] += a.marks_obtained

        # convert to percentage
        for sid in test_student_percentages:
            test_student_percentages[sid] = (test_student_percentages[sid] / max_marks) * 100

        sorted_perc = sorted(test_student_percentages.values(), reverse=True)
        rank = sorted_perc.index(percentage) + 1 if percentage in sorted_perc else "-"

        test_records.append({
            "test_name": test.title,
            "date": test.created_at.strftime("%Y-%m-%d"),
            "score": obtained,
            "max_marks": max_marks,
            "percentage": percentage,
            "rank": f"{rank}{ordinal_suffix(rank)}" if rank != "-" else "-",
            "status": "Passed" if percentage >= 35 else "Failed"
        })

    overall_percentage = round(sum(percentages) / len(percentages), 2) if percentages else 0

    return render_template(
        "student/student_performance.html",
        student=student,
        classroom=classroom,
        overall_percentage=overall_percentage,
        total_tests=len(test_records),
        best_score=best_score,
        best_test_name=best_test_name,
        student_rank=student_rank,
        rank_suffix=rank_suffix,
        test_records=test_records
    )





# -----------------------
# Logout
# -----------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    resp = make_response(redirect(url_for("landing")))  # Redirects to landing.html
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


# Optional: test DB connection
@app.route("/db-test")
def db_test():
    try:
        db.session.execute("SELECT 1")
        return "Database connected successfully!"
    except Exception as e:
        return f"Database connection failed: {e}"


# -----------------------
# Run App
# -----------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)



