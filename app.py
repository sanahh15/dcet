from flask import Flask, flash, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from authlib.integrations.flask_client import OAuth

from datetime import timedelta, datetime
from flask import send_from_directory
import sqlite3
import random
import os

# TestResult model defined below to avoid circular import
print("Current Template Folder:", os.path.abspath("templates"))

# Use request-time connections via `get_db()`; avoid running DB queries at import.
app = Flask(__name__)
app.secret_key = "dcet_secret_key"

app.permanent_session_lifetime = timedelta(days=7)  # login valid for 7 days
# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
oauth = OAuth(app)

# JumpCloud OIDC configuration
jumpcloud = oauth.register(
    name='jumpcloud',
    client_id='JUMPCLOUD_CLIENT_ID',
    client_secret='JUMPCLOUD_CLIENT_SECRET',
    access_token_url='https://oauth.jumpcloud.com/token',
    authorize_url='https://oauth.jumpcloud.com/auth',
    api_base_url='https://oauth.jumpcloud.com/',
    client_kwargs={'scope': 'openid profile email'},
)
db = SQLAlchemy(app)

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        admin = Admin.query.filter_by(email=email).first()
        if admin and admin.password == password:
            session['admin_id'] = admin.id
            return redirect('/admin_dashboard')

        instructor = Instructor.query.filter_by(email=email).first()
        if instructor and instructor.password == password:
            session['instructor_id'] = instructor.id
            return redirect('/instructor_dashboard')

        student = Student.query.filter_by(email=email).first()
        if student and student.password == password:
            session['student_id'] = student.id
            session['student_name'] = student.name
            return redirect('/student_dashboard')

        flash("Invalid Email or Password")

    return render_template('login.html')

# legacy login aliases will redirect to unified login
@app.route('/student_login')
@app.route('/admin/login')
@app.route('/instructor/login')
# some users might type just /admin or old /admin_dashboard
@app.route('/admin')
@app.route('/admin_dashboard')
def legacy_login():
    # If an admin or instructor is already authenticated, send them directly to the
    # real dashboard; otherwise fall back to unified login page.
    if 'admin_id' in session or 'instructor_id' in session:
        return redirect('/admin/dashboard')
    return redirect('/login')



# ---------------- MODELS ----------------
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
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    subjects = db.relationship('Subject', backref='branch', lazy=True)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text)
    pdf_file = db.Column(db.String(200))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))



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


class MCQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100))
    
    question = db.Column(db.Text)
    option1 = db.Column(db.String(200))
    option2 = db.Column(db.String(200))
    option3 = db.Column(db.String(200))
    option4 = db.Column(db.String(200))
    correct_answer = db.Column(db.String(200))



@app.route('/take_test/<subject_name>')
def take_test(subject_name):
    if 'student_id' not in session:
        return redirect('/login')

    # This filters questions so student only sees the selected DCET subject
    questions = Question.query.filter_by(subject=subject_name).all()
    
    # If no questions exist for a subject yet, we handle it gracefully
    if not questions:
        return "<h3>No questions added for " + subject_name + " yet.</h3>"

    return render_template('test.html', questions=questions, subject=subject_name)
# ✅ Corrected: DCETMaterial now top-level, not inside Material

# ---------------- CREATE DB + ADMIN ----------------
# Initialization moved into the main entrypoint to prevent multiple
# processes (e.g. the Flask debugger reloader) from racing to write
# the database.  When debug=True the reloader spawns two interpreters;
# executing this code at import time caused a "database is locked" error
# because both were trying to create/seed the database concurrently.
# We'll call `init_db()` below inside `if __name__ == '__main__'`.

def init_db():
    """Create tables and seed default data. Must be called from an
    active application context and only once (see __main__ guard)."""
    with app.app_context():
        db.create_all()

        # Admin account
        if not Admin.query.filter_by(email="admin@gmail.com").first():
            admin = Admin(email="admin@gmail.com", password="admin123")
            db.session.add(admin)

        # Create test branches if they don't exist
        test_branches = ['CSE', 'ECE', 'Mechanical', 'Civil', 'Electrical']
        for branch_name in test_branches:
            if not Branch.query.filter_by(name=branch_name).first():
                new_branch = Branch(name=branch_name)
                db.session.add(new_branch)

        # the commits may be grouped together safely
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

# ---------------- ROUTES ----------------


# -------- ADMIN --------

@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin_id' not in session and 'instructor_id' not in session:
        return redirect('/login')

    # ---------------- POST ACTIONS (UNCHANGED) ----------------
    if request.method == 'POST':
        branch_name = request.form.get('branch')
        subject_name = request.form.get('subject')
        branch_id = request.form.get('branch_id')

        # Add new branch
        if branch_name:
            if not Branch.query.filter_by(name=branch_name).first():
                new_branch = Branch(name=branch_name)
                db.session.add(new_branch)
                db.session.commit()

        # Add new subject
        if subject_name and branch_id:
            try:
                new_subject = Subject(
                    name=subject_name,
                    branch_id=int(branch_id)
                )
                db.session.add(new_subject)
                db.session.commit()
            except:
                db.session.rollback()

    # ---------------- EXISTING DATA (UNCHANGED) ----------------
    branches = Branch.query.all()

    for branch in branches:
        branch.subjects = Subject.query.filter_by(
            branch_id=branch.id
        ).all()

    subjects = Subject.query.all()

    # ---------------- NEW UPGRADE (MCQ RESULTS) ----------------
    mcq_results = MCQResult.query.order_by(
        MCQResult.attended_on.desc()
    ).all()

    total_attended = len(mcq_results)

    # ---------------- RENDER ----------------
    return render_template(
        'admin_dashboard.html',
        branches=branches,
        subjects=subjects,
        mcq_results=mcq_results,
        total_attended=total_attended
    )



# -------- STUDENT --------

@app.route('/student')
def student():
    if 'user' not in session:
        return redirect('/login')

    return render_template('student.html')

from datetime import datetime  # Make sure this is at the top of your app.py

@app.route('/student_dashboard')
def student_dashboard():
    if 'student_id' not in session:
        return redirect('/login')

    student = db.session.get(Student, session['student_id'])
    if not student:
        session.clear()
        return redirect('/login')
    
    # 1. Get today's date to look for targets
    today = datetime.now().date()
    
    # 2. Fetch today's target based on the student's branch
    current_target = DailyTarget.query.filter_by(
        target_date=today, 
        branch_id=student.branch_id
    ).first()
    
    # 3. Keep your existing subjects logic
    subjects = []
    if student.branch_id:
        subjects = Subject.query.filter_by(branch_id=student.branch_id).all()

    # 4. Pass 'target' to the HTML
    return render_template('student_dashboard.html', 
                           student_name=student.name,
                           subjects=subjects,
                           target=current_target) # <--- Added this

@app.after_request
def add_header(response):
    """
    Directs the browser to NOT cache any pages.
    This prevents the "Back" button from showing logged-in pages after logout.
    """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/student_logout')
def student_logout():
    session.clear()
    return redirect('/login')

@app.route('/subjects')
def subjects():
    return render_template('subjects.html')

@app.route('/materials/<branch>')
def materials(branch):
    return render_template('materials.html', branch=branch)

@app.route('/logout')
def logout():
    session.clear() # Deletes all student data from the session
    return redirect('/login')




@app.route('/authorize')
def authorize():
    token = jumpcloud.authorize_access_token()
    user = jumpcloud.get('userinfo').json()

    session['user'] = user
    return redirect('/student')

@app.route("/callback")
def callback():
    token = oauth.jumpcloud.authorize_access_token()
    user = oauth.jumpcloud.parse_id_token(token)

class DailyTarget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer)
    subject = db.Column(db.String(100))
    topic = db.Column(db.String(200))
    target_date = db.Column(db.Date)


@app.route('/student/register', methods=['GET', 'POST'])
def student_register():
    branches = Branch.query.all()  # get branches from DB

    if request.method == 'POST':
        name = request.form['name']
        dob = request.form['dob']
        gender = request.form['gender']
        branch_id = request.form['branch_id']  # this is now ID
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm_password']

        if password != confirm:
            return render_template('student_register.html', error="Passwords do not match", branches=branches)

        if Student.query.filter_by(email=email).first():
            return render_template('student_register.html', error="Email already registered", branches=branches)

        # Create student
        student = Student(
            name=name,
            dob=dob,
            gender=gender,
            email=email,
            password=password,
            branch_id=branch_id  # store ID
        )
        db.session.add(student)
        db.session.commit()

        print("Student registered successfully")

        return redirect(url_for('login'))

    return render_template('student_register.html', branches=branches)

@app.route('/admin/subject/<int:subject_id>/add-material', methods=['GET', 'POST'])
def admin_add_material(subject_id):
    subject = Subject.query.get_or_404(subject_id)

    if request.method == 'POST':
        title = request.form['title']
        question = request.form['question']
        
        answer = request.form.get('answer')

        file = request.files.get('qp_file')
        filename = None

        material = Material(
            title=title,
            question=question,
            answer=answer,
            pdf_file=filename,
            subject_id=subject.id
        )

        db.session.add(material)
        db.session.commit()

        return redirect(f'/admin/subject/{subject.id}/materials')

    return render_template('admin_add_material.html', subject=subject)
           

@app.route('/student/branch/<branch_name>')
def student_branch(branch_name):
    if 'student_id' not in session:
        return redirect('/login')

    branch = Branch.query.filter_by(name=branch_name).first()
    if not branch:
        return redirect('/student_dashboard')
    
    subjects = Subject.query.filter_by(branch_id=branch.id).all()

    return render_template(
        'student_branch.html',
        branch=branch_name,
        subjects=subjects
    )

@app.route('/student/subject/<int:subject_id>')
def student_subject(subject_id):
    if 'student_id' not in session:
        return redirect('/login')

    subject = db.session.get(Subject, subject_id)
    if not subject:
        return redirect('/student_dashboard')
    
    materials = Material.query.filter_by(subject_id=subject_id).all()
    dcet_materials = DCETMaterial.query.filter_by(subject_id=subject_id).all()

    return render_template(
        'student_subject.html',
        subject=subject,
        materials=materials,
        dcet_materials=dcet_materials
    )

@app.route('/student/dcet/<int:material_id>')
def student_dcet(material_id):
    if 'student_id' not in session:
        return redirect('/login')

    material = DCETMaterial.query.get_or_404(material_id)
    return render_template('student_dcet.html', material=material)

@app.route('/admin/edit-branch/<int:branch_id>', methods=['GET', 'POST'])
def edit_branch(branch_id):
    if 'admin_id' not in session:
        return redirect('/login')

    branch = Branch.query.get_or_404(branch_id)

    if request.method == 'POST':
        new_name = request.form['branch_name']
        branch.name = new_name
        db.session.commit()
        return redirect('/admin/dashboard')

    return render_template('edit_branch.html', branch=branch)

# Delete a branch
# ...existing code...
@app.route('/admin/delete-branch/<int:branch_id>', methods=['POST'])
def delete_branch(branch_id):
    if 'admin_id' not in session:
        return redirect('/login')

    branch = Branch.query.get_or_404(branch_id)

    # Delete all subjects and their related materials, then delete branch
    for subject in list(branch.subjects):
        for m in DCETMaterial.query.filter_by(subject_id=subject.id).all():
            # remove uploaded file if exists
            if m.qp_file:
                try:
                    import os
                    os.remove(m.qp_file)
                except Exception:
                    pass
            db.session.delete(m)
        for m in Material.query.filter_by(subject_id=subject.id).all():
            if m.pdf_file:
                try:
                    import os
                    os.remove(m.pdf_file)
                except Exception:
                    pass
            db.session.delete(m)
        db.session.delete(subject)

    db.session.delete(branch)
    db.session.commit()
    return redirect('/admin/dashboard')
# ...existing code...


# Delete a subject
@app.route('/admin/delete-subject/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    if 'admin_id' not in session:
        return redirect('/login')

    subject = Subject.query.get_or_404(subject_id)

    # Optional: delete all materials under this subject
    for material in DCETMaterial.query.filter_by(subject_id=subject.id).all():
        db.session.delete(material)

    db.session.delete(subject)
    db.session.commit()
    return redirect('/admin/dashboard')


@app.route('/admin/add-dcet/<int:subject_id>', methods=['GET', 'POST'])
def add_dcet(subject_id):
    if 'admin_id' not in session:
        return redirect('/login')

    subject = Subject.query.get_or_404(subject_id)

    if request.method == 'POST':
        title = request.form.get('title')
        question = request.form.get('question')
        answer = request.form.get('answer', '')
        qp_file = request.files.get('qp_file')

        filename = None
        if qp_file and qp_file.filename:
            import os
            os.makedirs('static/uploads', exist_ok=True)

            filename = qp_file.filename              # ✅ ONLY filename
            file_path = os.path.join('static', 'uploads', filename)
            qp_file.save(file_path)

        new_material = DCETMaterial(
            subject_id=subject.id,
            title=title,
            question=question,
            answer=answer,
            qp_file=filename                           # ✅ store filename only
        )

        db.session.add(new_material)
        db.session.commit()

        return redirect(f'/admin/subject/{subject.id}/materials')

    return render_template('admin_add_dcet.html', subject=subject)
@app.route('/admin/subject/<int:subject_id>/materials')
def admin_subject_materials(subject_id):
    if 'admin_id' not in session:
        return redirect('/login')

    subject = Subject.query.get_or_404(subject_id)
    materials = DCETMaterial.query.filter_by(subject_id=subject_id).all()

    return render_template('admin_subject_materials.html', 
                           subject=subject,
                           materials=materials)

@app.route('/admin/delete-dcet/<int:material_id>', methods=['POST'])
def delete_dcet(material_id):
    if 'admin_id' not in session:
        return redirect('/login')

    material = DCETMaterial.query.get_or_404(material_id)
    subject_id = material.subject_id

    # Optional: delete the uploaded file if exists
    if material.qp_file:
        import os
        try:
            os.remove(material.qp_file)
        except Exception as e:
            print(f"[LOG] Could not delete file: {e}")

    db.session.delete(material)
    db.session.commit()

    return redirect(f'/admin/subject/{subject_id}/materials')


# ...existing code...

import random

# 1. THE QUESTION BANK (C20 Syllabus - 20 Questions per Subject)
question_bank = {
    "maths": [
        {"id": 1, "q": "The value of the determinant of a singular matrix is?", "options": ["1", "0", "-1", "Any value"], "ans": "0"},
        {"id": 2, "q": "If A is a 3x3 matrix and |A|=5, then |2A| is?", "options": ["10", "20", "40", "80"], "ans": "40"},
        {"id": 3, "q": "The derivative of log(sin x) is?", "options": ["tan x", "cot x", "sec x", "cos x"], "ans": "cot x"},
        {"id": 4, "q": "The order of the differential equation d2y/dx2 + (dy/dx)3 = 0 is?", "options": ["1", "2", "3", "0"], "ans": "2"},
        {"id": 5, "q": "The value of ∫(1/x) dx is?", "options": ["x", "log x", "ex", "1"], "ans": "log x"},
        {"id": 6, "q": "A square matrix A is skew-symmetric if?", "options": ["AT = A", "AT = -A", "A = 0", "A = I"], "ans": "AT = -A"},
        {"id": 7, "q": "The value of sin(30°) is?", "options": ["1", "0.5", "0.866", "0"], "ans": "0.5"},
        {"id": 8, "q": "Integration of cos x is?", "options": ["sin x", "-sin x", "tan x", "sec x"], "ans": "sin x"},
        {"id": 9, "q": "The slope of a horizontal line is?", "options": ["1", "0", "Infinity", "-1"], "ans": "0"},
        {"id": 10, "q": "The characteristic equation of a matrix A is given by?", "options": ["|A-λI|=0", "|A|=0", "Aλ=0", "I-λA=0"], "ans": "|A-λI|=0"},
        {"id": 11, "q": "If y = x^n, then dy/dx is?", "options": ["nx", "nx^(n-1)", "x^(n+1)", "n/x"], "ans": "nx^(n-1)"},
        {"id": 12, "q": "The sum of the eigenvalues of a matrix is equal to its?", "options": ["Rank", "Trace", "Determinant", "Inverse"], "ans": "Trace"},
        {"id": 13, "q": "Value of e^0 is?", "options": ["0", "1", "Infinity", "e"], "ans": "1"},
        {"id": 14, "q": "The distance formula between two points is derived from?", "options": ["Euler's Theorem", "Pythagoras Theorem", "Taylor Series", "Leibniz Rule"], "ans": "Pythagoras Theorem"},
        {"id": 15, "q": "The derivative of tan x is?", "options": ["sec x", "sec^2 x", "cot x", "cosec x"], "ans": "sec^2 x"},
        {"id": 16, "q": "Formula for cos(2A) is?", "options": ["2sinAcosA", "cos^2A - sin^2A", "1+tan^2A", "2cosA"], "ans": "cos^2A - sin^2A"},
        {"id": 17, "q": "The rank of a 3x3 identity matrix is?", "options": ["1", "2", "3", "0"], "ans": "3"},
        {"id": 18, "q": "Integral of e^x is?", "options": ["e^x", "xe^x", "e^x/x", "log x"], "ans": "e^x"},
        {"id": 19, "q": "A matrix which has only one row is called?", "options": ["Column matrix", "Row matrix", "Square matrix", "Zero matrix"], "ans": "Row matrix"},
        {"id": 20, "q": "The value of cos(90°) is?", "options": ["1", "0", "-1", "0.5"], "ans": "0"}
    ],
    "statistics_analytics": [
        {"id": 41, "q": "The mean of 10, 20, 30 is?", "options": ["10", "20", "30", "60"], "ans": "20"},
        {"id": 42, "q": "The middle value of a sorted data set is?", "options": ["Mean", "Median", "Mode", "Range"], "ans": "Median"},
        {"id": 43, "q": "The value that appears most frequently in data is?", "options": ["Mean", "Median", "Mode", "Standard Deviation"], "ans": "Mode"},
        {"id": 44, "q": "Which of the following is a measure of dispersion?", "options": ["Mean", "Median", "Variance", "Mode"], "ans": "Variance"},
        {"id": 45, "q": "Probability of an impossible event is?", "options": ["1", "0.5", "0", "-1"], "ans": "0"},
        {"id": 46, "q": "Range is the difference between?", "options": ["Mean & Median", "Max & Min", "Mode & Mean", "None"], "ans": "Max & Min"},
        {"id": 47, "q": "Data visualization tool used in analytics is?", "options": ["Word", "Excel", "Tableau", "Notepad"], "ans": "Tableau"},
        {"id": 48, "q": "Standard deviation is the square root of?", "options": ["Mean", "Variance", "Range", "Mode"], "ans": "Variance"},
        {"id": 49, "q": "A pie chart represents data in terms of?", "options": ["Lines", "Bars", "Sectors/Angles", "Dots"], "ans": "Sectors/Angles"},
        {"id": 50, "q": "Normal distribution curve is?", "options": ["U-shaped", "Bell-shaped", "Straight line", "Circular"], "ans": "Bell-shaped"},
        {"id": 51, "q": "Correlation coefficient ranges between?", "options": ["0 to 1", "-1 to 1", "-infinity to infinity", "1 to 10"], "ans": "-1 to 1"},
        {"id": 52, "q": "Process of cleaning raw data is called?", "options": ["Data Mining", "Data Wrangling", "Data Printing", "Data Storage"], "ans": "Data Wrangling"},
        {"id": 53, "q": "Predicting future trends based on past data is?", "options": ["Descriptive Analytics", "Predictive Analytics", "Diagnostic Analytics", "Prescriptive Analytics"], "ans": "Predictive Analytics"},
        {"id": 54, "q": "Total probability of all outcomes is?", "options": ["0", "0.5", "1", "100"], "ans": "1"},
        {"id": 55, "q": "Arithmetic mean of first 5 natural numbers is?", "options": ["2", "3", "4", "5"], "ans": "3"},
        {"id": 56, "q": "A histogram is used for?", "options": ["Qualitative data", "Frequency distribution", "Linear regression", "Pie charts"], "ans": "Frequency distribution"},
        {"id": 57, "q": "Outliers are data points that are?", "options": ["Common", "In the center", "Significantly different", "Missing"], "ans": "Significantly different"},
        {"id": 58, "q": "The 'P' in P-value stands for?", "options": ["Percent", "Probability", "Process", "Position"], "ans": "Probability"},
        {"id": 59, "q": "Regression analysis is used for?", "options": ["Sorting", "Finding relationships", "Adding data", "Deleting data"], "ans": "Finding relationships"},
        {"id": 60, "q": "What is 'Big Data' characterized by?", "options": ["Volume, Velocity, Variety", "Size, Color, Shape", "Speed, Price, Value", "None"], "ans": "Volume, Velocity, Variety"}
    ],
    "feee": [
        {"id": 81, "q": "Unit of electrical power is?", "options": ["Volt", "Ampere", "Ohm", "Watt"], "ans": "Watt"},
        {"id": 82, "q": "The flow of electrons is called?", "options": ["Voltage", "Resistance", "Current", "Capacitance"], "ans": "Current"},
        {"id": 83, "q": "A step-up transformer increases?", "options": ["Current", "Power", "Voltage", "Frequency"], "ans": "Voltage"},
        {"id": 84, "q": "Ohm's law is not applicable to?", "options": ["Resistors", "Semiconductors", "Copper wires", "Heaters"], "ans": "Semiconductors"},
        {"id": 85, "q": "The power factor is the ratio of?", "options": ["True power to Apparent power", "Voltage to Current", "Resistance to Impedance", "Both A and C"], "ans": "Both A and C"},
        {"id": 86, "q": "Which material is a good conductor?", "options": ["Glass", "Copper", "Rubber", "Wood"], "ans": "Copper"},
        {"id": 87, "q": "A capacitor stores energy in?", "options": ["Magnetic field", "Electric field", "Chemical form", "Heat"], "ans": "Electric field"},
        {"id": 88, "q": "Full form of MCB is?", "options": ["Main Circuit Board", "Miniature Circuit Breaker", "Manual Control Box", "Mini Circuit Battery"], "ans": "Miniature Circuit Breaker"},
        {"id": 89, "q": "Frequency of DC is?", "options": ["50 Hz", "60 Hz", "0 Hz", "100 Hz"], "ans": "0 Hz"},
        {"id": 90, "q": "Function of a Rectifier is?", "options": ["AC to DC", "DC to AC", "Low to High", "High to Low"], "ans": "AC to DC"},
        {"id": 91, "q": "Unit of resistance is?", "options": ["Ohm", "Farad", "Henry", "Tesla"], "ans": "Ohm"},
        {"id": 92, "q": "Lead-acid battery is a?", "options": ["Primary cell", "Secondary cell", "Dry cell", "None"], "ans": "Secondary cell"},
        {"id": 93, "q": "KCL is based on the law of conservation of?", "options": ["Energy", "Charge", "Mass", "Momentum"], "ans": "Charge"},
        {"id": 94, "q": "Silicon is a?", "options": ["Conductor", "Insulator", "Semiconductor", "Superconductor"], "ans": "Semiconductor"},
        {"id": 95, "q": "Resistance of an ideal Ammeter is?", "options": ["Infinite", "Zero", "100 Ohm", "1 Ohm"], "ans": "Zero"},
        {"id": 96, "q": "Which is an active component?", "options": ["Resistor", "Inductor", "Transistor", "Capacitor"], "ans": "Transistor"},
        {"id": 97, "q": "The 'RMS' value stands for?", "options": ["Real Mean Square", "Root Mean Square", "Ready Made Supply", "Root Main Square"], "ans": "Root Mean Square"},
        {"id": 98, "q": "Inductance is measured in?", "options": ["Farad", "Henry", "Weber", "Ohm"], "ans": "Henry"},
        {"id": 99, "q": "Earthing is provided for?", "options": ["Safety", "Decoration", "High Voltage", "Reducing Current"], "ans": "Safety"},
        {"id": 100, "q": "Which law states V=IR?", "options": ["Faraday's Law", "Lenz's Law", "Ohm's Law", "Coulomb's Law"], "ans": "Ohm's Law"}
    ],
    "project_management": [
        {"id": 121, "q": "The first phase of Project Management is?", "options": ["Planning", "Execution", "Initiation", "Closure"], "ans": "Initiation"},
        {"id": 122, "q": "What does SMART stand for in goals?", "options": ["Simple, Manageable, Agile, Rigid, True", "Specific, Measurable, Achievable, Relevant, Time-bound", "Small, Medium, Average, Real, Total", "None"], "ans": "Specific, Measurable, Achievable, Relevant, Time-bound"},
        {"id": 123, "q": "A bar chart that shows a project schedule is?", "options": ["Pie Chart", "Gantt Chart", "Flow Chart", "PERT Chart"], "ans": "Gantt Chart"},
        {"id": 124, "q": "The longest path in a project network is the?", "options": ["Shortest path", "Critical path", "Slack path", "Fast track"], "ans": "Critical path"},
        {"id": 125, "q": "Who is responsible for the overall success of a project?", "options": ["Client", "Project Manager", "Developer", "Stakeholder"], "ans": "Project Manager"},
        {"id": 126, "q": "A document that authorizes the project is?", "options": ["Project Charter", "SOP", "Log book", "Invoice"], "ans": "Project Charter"},
        {"id": 127, "q": "Scope creep refers to?", "options": ["Project finishing early", "Uncontrolled changes in project scope", "Budget reduction", "Team expansion"], "ans": "Uncontrolled changes in project scope"},
        {"id": 128, "q": "Risk Management involves?", "options": ["Identification", "Assessment", "Mitigation", "All of the above"], "ans": "All of the above"},
        {"id": 129, "q": "WBS stands for?", "options": ["Work Breakdown Structure", "Weekly Budget System", "Work Build Schedule", "Web Based System"], "ans": "Work Breakdown Structure"},
        {"id": 130, "q": "KPI stands for?", "options": ["Key Performance Indicator", "Key Project Item", "Knowledge Process Index", "None"], "ans": "Key Performance Indicator"},
        {"id": 131, "q": "Meeting that happens at the end of a project?", "options": ["Kick-off", "Sprint", "Post-mortem / Lessons learned", "Stand-up"], "ans": "Post-mortem / Lessons learned"},
        {"id": 132, "q": "Agile is a ___ methodology.", "options": ["Sequential", "Iterative", "Fixed", "Slow"], "ans": "Iterative"},
        {"id": 133, "q": "Quality control ensures?", "options": ["Project is fast", "Project meets standards", "Project is cheap", "None"], "ans": "Project meets standards"},
        {"id": 134, "q": "People interested in or affected by the project are?", "options": ["Competitors", "Stakeholders", "Strangers", "Managers"], "ans": "Stakeholders"},
        {"id": 135, "q": "CPM stands for?", "options": ["Critical Path Method", "Cost Per Month", "Control Project Management", "Common Project Model"], "ans": "Critical Path Method"},
        {"id": 136, "q": "SWOT analysis stands for?", "options": ["Strengths, Weaknesses, Opportunities, Threats", "Small, Weak, Open, Tough", "Simple, Wide, Only, True", "None"], "ans": "Strengths, Weaknesses, Opportunities, Threats"},
        {"id": 137, "q": "A 'Kick-off' meeting happens at?", "options": ["End", "Middle", "Start", "Never"], "ans": "Start"},
        {"id": 138, "q": "Which is a project constraint?", "options": ["Time", "Cost", "Scope", "All of the above"], "ans": "All of the above"},
        {"id": 139, "q": "Backlog is a term used in?", "options": ["Waterfall", "Agile/Scrum", "Construction", "History"], "ans": "Agile/Scrum"},
        {"id": 140, "q": "Project closure includes?", "options": ["Releasing resources", "Archiving documents", "Formal handover", "All of the above"], "ans": "All of the above"}
    ],
    "it_skills": [
        {"id": 161, "q": "Which is not an OS?", "options": ["Linux", "Windows", "Oracle", "Android"], "ans": "Oracle"},
        {"id": 162, "q": "Full form of URL is?", "options": ["Uniform Resource Locator", "United Resource Link", "Universal Radio Link", "None"], "ans": "Uniform Resource Locator"},
        {"id": 163, "q": "Short cut for permanent delete?", "options": ["Delete", "Shift + Delete", "Ctrl + Delete", "Alt + Delete"], "ans": "Shift + Delete"},
        {"id": 164, "q": "Python is a ___ level language.", "options": ["Low", "High", "Machine", "Assembly"], "ans": "High"},
        {"id": 165, "q": "Which is used to create a presentation?", "options": ["MS Word", "MS Excel", "MS PowerPoint", "MS Access"], "ans": "MS PowerPoint"},
        {"id": 166, "q": "Firewall is used for?", "options": ["Security", "Data sharing", "Cooling", "Translation"], "ans": "Security"},
        {"id": 167, "q": "Cloud storage example?", "options": ["Hard disk", "Google Drive", "RAM", "ROM"], "ans": "Google Drive"},
        {"id": 168, "q": "Full form of BIOS is?", "options": ["Basic Input Output System", "Binary Input Output System", "Base Internal Operating System", "None"], "ans": "Basic Input Output System"},
        {"id": 169, "q": "A website's first page is called?", "options": ["Design page", "Home page", "Contact page", "Main page"], "ans": "Home page"},
        {"id": 170, "q": "Malware stands for?", "options": ["Malicious Software", "Multi Software", "Main Software", "Manual Software"], "ans": "Malicious Software"},
        {"id": 171, "q": "Protocol used for sending emails?", "options": ["HTTP", "FTP", "SMTP", "IP"], "ans": "SMTP"},
        {"id": 172, "q": "Which is a database management system?", "options": ["Chrome", "MySQL", "VLC", "Photoshop"], "ans": "MySQL"},
        {"id": 173, "q": "A pixel is?", "options": ["A hardware", "Smallest element of an image", "A computer virus", "A type of storage"], "ans": "Smallest element of an image"},
        {"id": 174, "q": "The speed of a processor is measured in?", "options": ["MB", "Gbps", "GHz", "Watts"], "ans": "GHz"},
        {"id": 175, "q": "Which is a social networking site?", "options": ["Amazon", "LinkedIn", "Wikipedia", "eBay"], "ans": "LinkedIn"},
        {"id": 176, "q": "Binary of decimal 2 is?", "options": ["01", "10", "11", "00"], "ans": "10"},
        {"id": 177, "q": "CAPTCHA is used to?", "options": ["Speed up login", "Distinguish humans from bots", "Decorate website", "Scan virus"], "ans": "Distinguish humans from bots"},
        {"id": 178, "q": "IOT stands for?", "options": ["Internet of Things", "Internal of Transfer", "International Online Tool", "None"], "ans": "Internet of Things"},
        {"id": 179, "q": "Which is not a search engine?", "options": ["Google", "Bing", "Safari", "DuckDuckGo"], "ans": "Safari"},
        {"id": 180, "q": "Ctrl + Z is the shortcut for?", "options": ["Redo", "Undo", "Paste", "Save"], "ans": "Undo"}
    ]
}


@app.route('/mcq-test/<subject_name>')
def mcq_test(subject_name):
    # Normalize the name to match your dictionary keys
    key = subject_name.lower().replace(' ', '_')
    subject_data = question_bank.get(key, [])

    if not subject_data:
        return "Subject not found in Question Bank", 404

    # Ensure we don't crash if there are fewer than 20 questions
    num_to_select = min(len(subject_data), 20)
    selected_questions = random.sample(subject_data, num_to_select)

    return render_template(
        'test.html',
        subject=subject_name.replace('_', ' ').upper(),
        questions=selected_questions
    )

@app.route('/submit-mcq', methods=['POST'])
def submit_mcq():
    score = 0
    total = 20
    
    # Calculate score by checking answers
    for form_key, user_ans in request.form.items():
        if form_key.startswith('question_'):
            q_id = int(form_key.split('_')[1])
            # Find question in the bank
            for sub in question_bank:
                for q_obj in question_bank[sub]:
                    if q_obj['id'] == q_id:
                        if q_obj['ans'] == user_ans:
                            score += 1

    # 1. Create the result object
    new_result = MCQResult(
        student_id=session.get('student_id'),
        subject=request.form.get('subject'),
        score=score,
        total=total,
        attended_on=datetime.now() # Ensure this is recorded
    )

    # 2. THE MOST IMPORTANT PART:
    try:
        db.session.add(new_result)
        db.session.commit()  # This "pushes" the data to the database
    except Exception as e:
        db.session.rollback()
        print(f"Error saving result: {e}")

    return render_template('results.html', score=score, total=total)

@app.route('/submit-results', methods=['POST'])
def submit_results():
    score = 0
    total = 20
    # Search all subjects in the bank to verify answers
    for form_key, user_ans in request.form.items():
        if form_key.startswith('question_'):
            q_id = int(form_key.split('_')[1])
            # Find question in the bank
            for sub in question_bank:
                for q_obj in question_bank[sub]:
                    if q_obj['id'] == q_id:
                        if q_obj['ans'] == user_ans:
                            score += 1
    return render_template('results.html', score=score, total=total)

@app.route('/submit', methods=['POST'])
def submit():
    # Logic to calcula
    # te score
    score = 0
    for key, value in request.form.items():
        # Check answers here
        pass
    return f"Test Submitted! You answered {len(request.form)} questions."

from datetime import datetime, date

# ---------------- ADMIN ADD TARGET ----------------
@app.route('/admin/add_target', methods=['GET', 'POST'])
def add_target():
    if request.method == 'POST':
        # Get data from the professional form
        branch_id = int(request.form['branch_id'])
        subject = request.form['subject']
        topic = request.form['topic']
        
        # Convert the date string from the form into a Python date
        date_str = request.form['target_date']
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Save to your DailyTarget table
        target = DailyTarget(
            branch_id=branch_id,
            subject=subject,
            topic=topic,
            target_date=target_date
        )

        db.session.add(target)
        db.session.commit()

        # Professional redirect back to see the result
        return "SUCCESS: DCET Target Added! <a href='/student_dashboard'>View Dashboard</a>"

    return render_template('admin_add_target.html')  

@app.route('/admin/mcq-results')
def admin_mcq_results():
    # Fetch all results, newest first
    results = MCQResult.query.order_by(MCQResult.attended_on.desc()).all()
    
    # Debugging: Print to your terminal to see if data exists
    print(f"Found {len(results)} results in database") 
    
    return render_template('admin_mcq_results.html', results=results)


@app.route("/admin_attendance")
def admin_attendance():

    mcq_results = MCQResult.query.all()

    total_attended = len(mcq_results)

    return render_template(
        "admin_attendance.html",
        mcq_results=mcq_results,
        total_attended=total_attended
    )


# 📌 use a consistent path with a subdirectory rather than an underscore



@app.route('/instructor_dashboard')
def instructor_dashboard():
    if 'instructor_id' not in session:
        # previously used an underscore path which conflicted with redirects
        return redirect('/login')


    return render_template('instructor_dashboard.html')

@app.route('/instructor/logout')
def instructor_logout():
    session.pop('instructor_id', None)
    # logout should send them to the new login path as well
    return redirect('/login')


@app.route('/instructor/add_mcq')
def select_subject_for_mcq():

    if 'instructor_id' not in session:
        return redirect('/login')

    subjects = [
        ("engineering_mathematics", "Engineering Mathematics"),
        ("statistics_analytics", "Statistics & Analytics"),
        ("it_skills", "IT Skills"),
        ("feee", "Fundamentals of Electrical & Electronics Engineering"),
        ("pms", "Project Management Skills")
    ]

    return render_template("select_subject.html", subjects=subjects)    

@app.route('/instructor/add_mcq/<subject_slug>', methods=['GET', 'POST'])
def add_mcq(subject_slug):

    subject_slugs = {
        "engineering_mathematics": "Engineering Mathematics",
        "statistics_analytics": "Statistics & Analytics",
        "it_skills": "IT Skills",
        "feee": "FEEE",
        "pms": "PMS"
    }

    subject = subject_slugs.get(subject_slug)

    if not subject:
        return "Invalid Subject"

    if request.method == 'POST':
        for i in range(1, 31):
            question = request.form[f'question{i}']
            option1 = request.form[f'option{i}_1']
            option2 = request.form[f'option{i}_2']
            option3 = request.form[f'option{i}_3']
            option4 = request.form[f'option{i}_4']
            correct = request.form[f'correct{i}']

            new_mcq = MCQ(
                subject=subject,
                question=question,
                option1=option1,
                option2=option2,
                option3=option3,
                option4=option4,
                correct_answer=correct
            )

            db.session.add(new_mcq)

        db.session.commit()

        added_count = 30
        final_count = MCQ.query.filter_by(subject=subject).count()
        return render_template('mcq_added_confirmation.html', subject=subject, added_count=added_count, final_count=final_count)

    return render_template("instructor_add_mcq.html", subject=subject)
# app and db are already defined at the top of this file, no need to re-import

@app.route('/student/test/<subject_slug>', methods=['GET', 'POST'])
def student_test(subject_slug):
    # Map slug to proper subject name
    subject = subject_slugs.get(subject_slug)
    if not subject:
        return "Invalid Subject"

    # Pick 30 questions for that subject
    questions = MCQ.query.filter_by(subject=subject).limit(30).all()

    if request.method == 'POST':
        score = 0
        for q in questions:
            selected = request.form.get(str(q.id))
            if selected == q.correct_answer:
                score += 1

        # Save result to database for instructor tracking
        result = TestResult(
            student_name=session.get('student_name', 'Student Name'),
            subject=subject,
            score=score,
            total=len(questions),
            date_taken=datetime.now()
        )
        db.session.add(result)
        db.session.commit()

        # Pass additional data to results template
        return render_template(
            'results.html',
            score=score,
            total=len(questions),
            subject=subject,
            student_name=session.get('student_name', 'Student Name'),  # fallback if not logged in
            test_date=datetime.now().strftime("%d %B %Y"),
            instructor_name="Sahana"  # replace with your name
        )

    return render_template('test.html', questions=questions, subject=subject)

@app.route('/instructor/test_results')
def instructor_test_results():
    # Fetch all test results, newest first
    results = TestResult.query.order_by(TestResult.date_taken.desc()).all()
    return render_template('instructor_test_results.html', results=results)

@app.route('/instructor/generate_mcqs')
def generate_mcqs_page():
    return render_template('generate_mcqs.html')

@app.route('/instructor/add_study_material', methods=['GET', 'POST'])
def add_study_material():
    if 'instructor_id' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        subject = request.form.get('subject')
        title = request.form.get('title')
        content = request.form.get('content')
        
        # You can store this in database if you have a StudyMaterial model
        # For now, just return success
        return render_template('material_added_confirmation.html', subject=subject, title=title)
    
    subjects = [
        ("Engineering Mathematics", "Engineering Mathematics"),
        ("Statistics & Analytics", "Statistics & Analytics"),
        ("IT Skills", "IT Skills"),
        ("FEEE", "FEEE"),
        ("PMS", "PMS")
    ]
    return render_template('instructor_add_study_material.html', subjects=subjects)

@app.route('/instructor/add_announcement', methods=['GET', 'POST'])
def add_announcement():
    if 'instructor_id' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        title = request.form.get('title')
        message = request.form.get('message')
        
        # You can store this in database if you have an Announcement model
        # For now, just return success
        return render_template('announcement_added_confirmation.html', title=title)
    
    return render_template('instructor_add_announcement.html')

from random import sample
@app.route('/instructor/generate_mcqs/<subject_slug>')
def generate_mcqs(subject_slug):
    subject = subject_slugs.get(subject_slug)
    if not subject:
        return "Invalid Subject"

    # Check if MCQs already exist for this subject
    existing = MCQ.query.filter_by(subject=subject).count()
    if existing >= 30:
        added_count = 0
        final_count = existing
    else:
        added_count = len(sample_mcqs[subject])
        for q in sample_mcqs[subject]:
            new_mcq = MCQ(
                subject=subject,
                question=q['question'],
                option1=q['options'][0],
                option2=q['options'][1],
                option3=q['options'][2],
                option4=q['options'][3],
                correct_answer=q['correct']
            )
            db.session.add(new_mcq)
        db.session.commit()
        final_count = existing + added_count
    return render_template('mcq_added_confirmation.html', subject=subject, added_count=added_count, final_count=final_count)

# Map slugs to proper subject names
subject_slugs = {
    "engineering_mathematics": "Engineering Mathematics",
    "statistics_analytics": "Statistics & Analytics",
    "it_skills": "IT Skills",
    "feee": "FEEE",
    "pms": "PMS"
}
sample_mcqs = {
    "Engineering Mathematics": [
        {"question": "Derivative of x^3?", "options": ["3x^2","x^2","x^3","3x"], "correct": "1"},
        {"question": "Integral of x dx?", "options": ["x^2","x^2/2","2x","1/x"], "correct": "2"},
        {"question": "Limit of (1+1/n)^n as n→∞?", "options": ["0","1","e","∞"], "correct": "3"},
        {"question": "Derivative of sin(x)?", "options": ["cos(x)","-cos(x)","sin(x)","-sin(x)"], "correct": "1"},
        {"question": "Integral of cos(x) dx?", "options": ["sin(x)","-sin(x)","cos(x)","-cos(x)"], "correct": "1"},
        {"question": "Derivative of e^x?", "options": ["e^x","xe","x^2","1"], "correct": "1"},
        {"question": "Integral of 1/x dx?", "options": ["ln(x)","x","1/x^2","e^x"], "correct": "1"},
        {"question": "Limit of sin(x)/x as x→0?", "options": ["0","1","∞","-1"], "correct": "2"},
        {"question": "Derivative of ln(x)?", "options": ["1/x","x","ln(x)","-1/x"], "correct": "1"},
        {"question": "Integral of e^x dx?", "options": ["e^x","x e^x","ln(x)","1"], "correct": "1"},
        {"question": "Derivative of cos(x)?", "options": ["-sin(x)","sin(x)","cos(x)","-cos(x)"], "correct": "1"},
        {"question": "Limit of (x^2 -1)/(x-1) as x→1?", "options": ["0","2","1","∞"], "correct": "2"},
        {"question": "Integral of x^2 dx?", "options": ["x^3/3","x^2/2","x^3","2x^2"], "correct": "1"},
        {"question": "Derivative of tan(x)?", "options": ["sec^2(x)","tan(x)","cos^2(x)","1"], "correct": "1"},
        {"question": "Integral of 1/(1+x^2) dx?", "options": ["arctan(x)","ln(x)","1/x","x"], "correct": "1"},
        {"question": "Limit of (1 - cos(x))/x^2 as x→0?", "options": ["0","1/2","1","∞"], "correct": "2"},
        {"question": "Derivative of x sin(x)?", "options": ["sin(x)+x cos(x)","x cos(x)","sin(x)","x sin(x)"], "correct": "1"},
        {"question": "Integral of sin(x) dx?", "options": ["-cos(x)","cos(x)","sin(x)","-sin(x)"], "correct": "1"},
        {"question": "Limit of (e^x-1)/x as x→0?", "options": ["0","1","∞","-1"], "correct": "2"},
        {"question": "Derivative of x^n?", "options": ["n x^(n-1)","x^n","n x^n","x^(n-1)"], "correct": "1"},
        {"question": "Integral of 1/(x^2) dx?", "options": ["-1/x","1/x","x","-x"], "correct": "1"},
        {"question": "Derivative of arcsin(x)?", "options": ["1/sqrt(1-x^2)","sqrt(1-x^2)","x","1"], "correct": "1"},
        {"question": "Limit of ln(1+x)/x as x→0?", "options": ["0","1","∞","-1"], "correct": "2"},
        {"question": "Integral of cos(2x) dx?", "options": ["sin(2x)/2","2 sin(x)","cos(2x)/2","sin(x)"], "correct": "1"},
        {"question": "Derivative of sec(x)?", "options": ["sec(x)tan(x)","sec(x)","tan(x)","1"], "correct": "1"},
        {"question": "Integral of 1/(sqrt(1-x^2)) dx?", "options": ["arcsin(x)","arccos(x)","x","1"], "correct": "1"},
        {"question": "Limit of x*sin(1/x) as x→0?", "options": ["0","1","∞","-1"], "correct": "1"},
        {"question": "Derivative of ln(sin(x))?", "options": ["cot(x)","tan(x)","1/sin(x)","-cot(x)"], "correct": "1"},
        {"question": "Integral of x e^x dx?", "options": ["x e^x - e^x","e^x","x e^x","-e^x"], "correct": "1"},
        {"question": "Limit of (x^2+3x)/(x) as x→0?", "options": ["0","3","∞","1"], "correct": "1"},
    ],

    "Statistics & Analytics": [
        {"question": "Mean of 2,4,6?", "options": ["2","4","6","12"], "correct": "2"},
        {"question": "Probability of head in coin toss?", "options": ["0.25","0.5","0.75","1"], "correct": "2"},
        {"question": "Median of 1,3,5?", "options": ["1","3","5","9"], "correct": "2"},
        {"question": "Variance of 2,4,6?", "options": ["1","2","4","8"], "correct": "3"},
        {"question": "Standard deviation is?", "options": ["sqrt(variance)","variance^2","mean","median"], "correct": "1"},
        {"question": "Random variable takes?", "options": ["Single value","Multiple values","Unknown","None"], "correct": "2"},
        {"question": "Mode of 1,1,2,3?", "options": ["1","2","3","0"], "correct": "1"},
        {"question": "Probability of rolling 6 on die?", "options": ["1/6","1/5","1/4","1/3"], "correct": "1"},
        {"question": "Cumulative frequency shows?", "options": ["Sum frequency","Mean","Median","Mode"], "correct": "1"},
        {"question": "Event with certain outcome?", "options": ["Impossible","Sure","Random","Dependent"], "correct": "2"},
        {"question": "Random experiment example?", "options": ["Toss coin","2+2","Derivative","Integral"], "correct": "1"},
        {"question": "Range of data?", "options": ["Max - Min","Mean","Variance","Median"], "correct": "1"},
        {"question": "Probability range?", "options": ["0 to 1","-1 to 1","0 to 100","-∞ to ∞"], "correct": "1"},
        {"question": "Outlier definition?", "options": ["Extreme value","Average","Median","Mode"], "correct": "1"},
        {"question": "Skewness measures?", "options": ["Symmetry","Variance","Mean","Median"], "correct": "1"},
        {"question": "Kurtosis measures?", "options": ["Peakedness","Variance","Mean","Median"], "correct": "1"},
        {"question": "Z-score represents?", "options": ["Standard deviation","Mean","Median","Mode"], "correct": "1"},
        {"question": "Correlation ranges?", "options": ["-1 to 1","0 to 1","0 to 100","-∞ to ∞"], "correct": "1"},
        {"question": "Regression predicts?", "options": ["Dependent","Independent","Both","None"], "correct": "1"},
        {"question": "Sampling method example?", "options": ["Random","Mean","Median","Mode"], "correct": "1"},
        {"question": "Poisson distribution used for?", "options": ["Rare events","Mean","Median","Mode"], "correct": "1"},
        {"question": "Binomial distribution?", "options": ["Two outcomes","Multiple outcomes","Continuous","None"], "correct": "1"},
        {"question": "Central Limit Theorem states?", "options": ["Sample mean → Normal","Population mean","Variance","Mode"], "correct": "1"},
        {"question": "Probability of complement?", "options": ["1-P(E)","P(E)","0","∞"], "correct": "1"},
        {"question": "Conditional probability?", "options": ["P(A|B)","P(B|A)","P(A)+P(B)","0"], "correct": "1"},
        {"question": "Covariance measures?", "options": ["Relationship","Variance","Mean","Median"], "correct": "1"},
        {"question": "Probability density function?", "options": ["Continuous probability","Discrete","Mean","Variance"], "correct": "1"},
        {"question": "Expected value?", "options": ["Mean","Variance","Median","Mode"], "correct": "1"},
        {"question": "What is a probability distribution?", "options": ["List of outcomes and probabilities","List of numbers","Graph only","None"], "correct": "1"},
        {"question": "A data set with values 2,2,3 has mode?", "options": ["2","3","Cannot determine","None"], "correct": "1"},
    ],

    "IT Skills": [
        {"question": "HTML stands for?", "options": ["HTML","CSS","JS","HTTP"], "correct": "1"},
        {"question": "CSS is used for?", "options": ["Style","Logic","Database","Networking"], "correct": "1"},
        {"question": "JS is used for?", "options": ["Interactivity","Database","Styling","Networking"], "correct": "1"},
        {"question": "Python is?", "options": ["Programming","Styling","Markup","Database"], "correct": "1"},
        {"question": "SQL is?", "options": ["Database","Styling","Programming","Networking"], "correct": "1"},
        {"question": "Bootstrap is?", "options": ["CSS Framework","Python library","DB","JS library"], "correct": "1"},
        {"question": "Responsive design?", "options": ["Adapt screen","Logic","DB","Networking"], "correct": "1"},
        {"question": "Hyperlink tag in HTML?", "options": ["<a>","<p>","<div>","<link>"], "correct": "1"},
        {"question": "Table row tag?", "options": ["<tr>","<td>","<th>","<table>"], "correct": "1"},
        {"question": "Form tag?", "options": ["<form>","<input>","<textarea>","<label>"], "correct": "1"},
        {"question": "JS function?", "options": ["function myFunc(){}","<function>","func()","def"], "correct": "1"},
        {"question": "DOM stands for?", "options": ["Document Object Model","Data Object Model","Design Object Model","None"], "correct": "1"},
        {"question": "HTTP stands for?", "options": ["HyperText Transfer Protocol","HyperText Test Protocol","HighText Transfer Protocol","None"], "correct": "1"},
        {"question": "URL stands for?", "options": ["Uniform Resource Locator","Uniform Resource Link","Universal Resource Locator","None"], "correct": "1"},
        {"question": "IP stands for?", "options": ["Internet Protocol","Internal Protocol","Internet Process","None"], "correct": "1"},
        {"question": "CPU stands for?", "options": ["Central Processing Unit","Central Performance Unit","Computer Processing Unit","None"], "correct": "1"},
        {"question": "RAM stands for?", "options": ["Random Access Memory","Read Access Memory","Read Array Memory","None"], "correct": "1"},
        {"question": "ROM stands for?", "options": ["Read Only Memory","Random Only Memory","Read Object Memory","None"], "correct": "1"},
        {"question": "DNS stands for?", "options": ["Domain Name System","Domain Number System","Data Name System","None"], "correct": "1"},
        {"question": "HTTP status 404?", "options": ["Page not found","Success","Server error","Redirect"], "correct": "1"},
        {"question": "Function of CSS?", "options": ["Styling","Logic","Database","Networking"], "correct": "1"},
        {"question": "JS variable?", "options": ["let","var","const","All"], "correct": "4"},
        {"question": "JS loop?", "options": ["for","while","do-while","All"], "correct": "4"},
        {"question": "JS array?", "options": ["[]","{}","()","<>"], "correct": "1"},
        {"question": "HTML image tag?", "options": ["<img>","<image>","<src>","<picture>"], "correct": "1"},
        {"question": "Input tag in form?", "options": ["<input>","<textarea>","<label>","<form>"], "correct": "1"},
        {"question": "CSS selector for id?", "options": ["#id"," .class","element","*"], "correct": "1"},
        {"question": "CSS selector for class?", "options": [".class","#id","element","*"], "correct": "1"},
        {"question": "JS event click?", "options": ["onclick","onhover","onchange","oninput"], "correct": "1"},
        {"question": "What does CSS stand for?", "options": ["Cascading Style Sheets","Computer Style Syntax","Colorful Style Scripts","None"], "correct": "1"},
    ],

    "PMS": [
        {"question": "Project Life Cycle phases?", "options": ["Initiation, Planning, Execution, Closure","Planning only","Execution only","All"], "correct": "1"},
        {"question": "Critical Path Method is for?", "options": ["Scheduling","Budgeting","Hiring","Coding"], "correct": "1"},
        {"question": "Gantt Chart shows?", "options": ["Timeline","Budget","Employees","All"], "correct": "1"},
        {"question": "Risk Management is?", "options": ["Identify & Control Risks","Budget","Coding","Design"], "correct": "1"},
        {"question": "Scope Management is?", "options": ["Project Scope","Time","Budget","Quality"], "correct": "1"},
        {"question": "Stakeholder definition?", "options": ["Person interested in project","Coding","Budget","Design"], "correct": "1"},
        {"question": "Resource Management?", "options": ["Allocate & Control Resources","Budget","Coding","Time"], "correct": "1"},
        {"question": "Work Breakdown Structure?", "options": ["Divide tasks","Budget","Coding","Design"], "correct": "1"},
        {"question": "Milestone in project?", "options": ["Key achievement","Task","Resource","Budget"], "correct": "1"},
        {"question": "Project Closure means?", "options": ["Finish project & document","Coding","Design","Time"], "correct": "1"},
        {"question": "Earned Value Analysis?", "options": ["Measure performance","Budget","Design","Coding"], "correct": "1"},
        {"question": "PERT chart is?", "options": ["Network diagram","Budget","Resource chart","Time chart"], "correct": "1"},
        {"question": "Project Baseline?", "options": ["Original plan","Budget","Coding","Design"], "correct": "1"},
        {"question": "Project Charter?", "options": ["Authorize project","Budget","Design","Coding"], "correct": "1"},
        {"question": "Project Budget?", "options": ["Allocate funds","Design","Coding","Time"], "correct": "1"},
        {"question": "Project Schedule?", "options": ["Timeline","Budget","Coding","Design"], "correct": "1"},
        {"question": "Change Management?", "options": ["Control changes","Budget","Coding","Design"], "correct": "1"},
        {"question": "Quality Management?", "options": ["Ensure quality","Budget","Coding","Design"], "correct": "1"},
        {"question": "Communication Plan?", "options": ["Share info","Budget","Coding","Design"], "correct": "1"},
        {"question": "Project Monitoring?", "options": ["Track progress","Budget","Coding","Design"], "correct": "1"},
        {"question": "Project Evaluation?", "options": ["Assess outcomes","Budget","Coding","Design"], "correct": "1"},
        {"question": "Project Reporting?", "options": ["Report status","Budget","Coding","Design"], "correct": "1"},
        {"question": "Project Documentation?", "options": ["Record details","Budget","Coding","Design"], "correct": "1"},
        {"question": "Project Resource Planning?", "options": ["Plan resources","Budget","Coding","Design"], "correct": "1"},
        {"question": "Project Kick-off?", "options": ["Start project","Budget","Coding","Design"], "correct": "1"},
        {"question": "Project Stakeholder Analysis?", "options": ["Identify stakeholders","Budget","Coding","Design"], "correct": "1"},
        {"question": "Project Risk Assessment?", "options": ["Identify risks","Budget","Coding","Design"], "correct": "1"},
        {"question": "Project Scope Statement?", "options": ["Document project scope","Budget","Coding","Design"], "correct": "1"},
        {"question": "Project Time Management?", "options": ["Manage schedule","Budget","Coding","Design"], "correct": "1"},
        {"question": "A stakeholder is?", "options": ["Interested party","Project manager","Developer","Designer"], "correct": "1"},
    ],

    "FEEE": [
    {"question": "Ohm's law states?", "options": ["V=IR","P=VI","E=MC2","F=ma"], "correct": "1"},
    {"question": "Unit of Electric Current?", "options": ["Volt","Ampere","Ohm","Watt"], "correct": "2"},
    {"question": "Unit of Voltage?", "options": ["Volt","Ampere","Ohm","Watt"], "correct": "1"},
    {"question": "Unit of Resistance?", "options": ["Ohm","Volt","Ampere","Watt"], "correct": "1"},
    {"question": "Power formula?", "options": ["P=VI","V=IR","E=MC2","F=ma"], "correct": "1"},
    {"question": "Series resistance formula?", "options": ["R_total = R1+R2+...","R_total = R1*R2","R_total = 1/R1 + 1/R2","R_total = V/I"], "correct": "1"},
    {"question": "Parallel resistance formula?", "options": ["1/R_total = 1/R1 + 1/R2","R_total = R1+R2","R_total = R1*R2","R_total = V/I"], "correct": "1"},
    {"question": "Electric power unit?", "options": ["Watt","Volt","Ampere","Ohm"], "correct": "1"},
    {"question": "Kirchhoff's Current Law states?", "options": ["Sum of currents at junction = 0","Voltage in loop=0","P=VI","F=ma"], "correct": "1"},
    {"question": "Kirchhoff's Voltage Law states?", "options": ["Sum of voltages in loop = 0","Current in junction=0","P=VI","V=IR"], "correct": "1"},
    {"question": "Capacitance unit?", "options": ["Farad","Henry","Watt","Volt"], "correct": "1"},
    {"question": "Inductance unit?", "options": ["Henry","Farad","Watt","Volt"], "correct": "1"},
    {"question": "Resistor color code: Red means?", "options": ["2","0","1","5"], "correct": "1"},
    {"question": "Resistor color code: Black means?", "options": ["0","1","2","5"], "correct": "1"},
    {"question": "Energy stored in capacitor formula?", "options": ["E=1/2 C V^2","E=CV","E=VI","E=IR"], "correct": "1"},
    {"question": "Reactance of capacitor formula?", "options": ["Xc = 1/(2πfC)","Xc = 2πfC","Xc = V/I","Xc = IR"], "correct": "1"},
    {"question": "Reactance of inductor formula?", "options": ["Xl = 2πfL","Xl = 1/(2πfL)","Xl = V/I","Xl = IR"], "correct": "1"},
    {"question": "Unit of frequency?", "options": ["Hertz","Volt","Ampere","Ohm"], "correct": "1"},
    {"question": "AC stands for?", "options": ["Alternating Current","Active Current","Ampere Current","Atomic Charge"], "correct": "1"},
    {"question": "DC stands for?", "options": ["Direct Current","Digital Current","Differential Current","Dependent Current"], "correct": "1"},
    {"question": "Power factor =?", "options": ["cosθ","sinθ","tanθ","1"], "correct": "1"},
    {"question": "Phase difference in pure resistor?", "options": ["0°","90°","180°","45°"], "correct": "1"},
    {"question": "Phase difference in pure inductor?", "options": ["90°","0°","180°","45°"], "correct": "1"},
    {"question": "Phase difference in pure capacitor?", "options": ["-90°","0°","90°","180°"], "correct": "1"},
    {"question": "Impedance unit?", "options": ["Ohm","Volt","Ampere","Watt"], "correct": "1"},
    {"question": "RMS value of AC?", "options": ["V_peak / √2","V_peak","V_peak*2","V_avg"], "correct": "1"},
    {"question": "Current leads voltage in?", "options": ["Capacitor","Inductor","Resistor","Both"], "correct": "1"},
    {"question": "Voltage leads current in?", "options": ["Inductor","Capacitor","Resistor","Both"], "correct": "1"},
    {"question": "Transformer works on?", "options": ["AC","DC","Both","None"], "correct": "1"},
    {"question": "Step-up transformer increases?", "options": ["Voltage","Current","Resistance","Power"], "correct": "1"},
]
}# end of sample_mcqs dictionary



if __name__ == '__main__':
    # when debug mode is enabled the reloader imports this module twice
    # (once in the parent process and once in the child). only initialize
    # the database in the *child* process where Werkzeug sets this
    # environment variable. this avoids SQLITE "database is locked"
    # errors that were occurring at startup.
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        init_db()

    # start the server after any required setup
    app.run(debug=True)    
