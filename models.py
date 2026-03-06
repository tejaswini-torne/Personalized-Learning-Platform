from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class McqTest(db.Model):
    __tablename__ = "mcq_tests"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey("classrooms.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # NEW: Only visible to students if posted
    is_posted = db.Column(db.Boolean, default=False)

    questions = db.relationship(
        "McqQuestion", backref="test", cascade="all, delete-orphan", lazy=True
    )



class McqQuestion(db.Model):
    __tablename__ = "mcq_questions"

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey("mcq_tests.id"), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.Text, default="mcq")  # mcq or text
    correct_option = db.Column(db.Text)  # for MCQ: option_id, for text: correct answer
    marks = db.Column(db.Integer, default=2)

    # One question → Many options
    options = db.relationship(
        "McqOption", backref="question", cascade="all, delete-orphan", lazy=True
    )


class McqOption(db.Model):
    __tablename__ = "mcq_options"

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("mcq_questions.id"), nullable=False)
    option_text = db.Column(db.Text, nullable=False)


class StudentAnswer(db.Model):
    __tablename__ = "student_answers"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey("mcq_tests.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("mcq_questions.id"), nullable=False)
    selected_option = db.Column(db.Text)
 # For MCQ: option number; For text: student's answer
    marks_obtained = db.Column(db.Integer, default=0)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)



from datetime import datetime
class StudentDoubt(db.Model):
    __tablename__ = "student_doubts"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # REQUIRED FIELD FOR TEACHER FILTERING
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=False)

    description = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(100))

    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    # TEACHER REPLY SYSTEM
    reply = db.Column(db.Text, nullable=True)
    reply_date = db.Column(db.DateTime, nullable=True)

    # DOUBT PROGRESS STATUS
    status = db.Column(db.String(20), default="Pending")   # Pending / Answered / Resolved


