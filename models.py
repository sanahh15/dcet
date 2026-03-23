from extensions import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    dob = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(10))
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20))
    branch = db.Column(db.String(50))
    password = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)

class MCQ(db.Model):
    __tablename__ = 'mcq'

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(50))
    question = db.Column(db.String(500))
    option1 = db.Column(db.String(200))
    option2 = db.Column(db.String(200))
    option3 = db.Column(db.String(200))
    option4 = db.Column(db.String(200))
   

class Subject(db.Model):
    __tablename__ = 'subject'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)

class InstructorSubject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    instructor_id = db.Column(db.Integer)
    subject_id = db.Column(db.Integer)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
   
class Student(db.Model):
    __tablename__ = 'student'
    __table_args__ = {'extend_existing': True}  # This allows redefinition

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    dob = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(10))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(50))
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'))


class Branch(db.Model):
    __tablename__ = 'branch'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    subjects = db.relationship('Subject', backref='branch', lazy=True)

class Material(db.Model):
    __tablename__ = 'material'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    question = db.Column(db.Text)
    answer = db.Column(db.Text)
    pdf_file = db.Column(db.String(200))

    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))

     # admin or instructor

class DCETMaterial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=True)
    qp_file = db.Column(db.String(200), nullable=True)
      # optional PDF

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(300))


class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    date_taken = db.Column(db.DateTime, default=datetime.utcnow)

class MCQResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    subject = db.Column(db.String(100))
    score = db.Column(db.Integer)
    total = db.Column(db.Integer)
    attended_on = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='mcq_results')

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Add or ensure this line exists:
    subject = db.Column(db.String(100), nullable=False) 
    q_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(200))
    option_b = db.Column(db.String(200))
    option_c = db.Column(db.String(200))
    option_d = db.Column(db.String(200))
    correct_ans = db.Column(db.String(200))

class Instructor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

class StudyMaterial(db.Model):
    __tablename__ = 'study_material'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    pdf_file = db.Column(db.String(200))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    uploaded_by = db.Column(db.String(50))  # admin or instructor

    subject = db.relationship('Subject', backref='study_materials') 

class DailyTarget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer)
    subject = db.Column(db.String(100))
    topic = db.Column(db.String(200))
    target_date = db.Column(db.Date)