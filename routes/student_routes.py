from datetime import datetime
from flask import Blueprint, render_template, request, redirect, session, url_for

from extensions import db
from models import Question, Student, Branch, Subject, Material, DCETMaterial, MCQ, TestResult,DailyTarget


student = Blueprint('student', __name__)

@student.route('/student_dashboard')
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

    subjects = Subject.query.filter_by(branch_id=student.branch_id).all()

    # 4. Pass 'target' to the HTML
    return render_template('student_dashboard.html', 
                           student_name=student.name,
                           subjects=subjects,
                           target=current_target) # <--- Added this


@student.route('/student/register', methods=['GET', 'POST'])
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

@student.route('/take_test/<subject_name>')
def take_test(subject_name):
    if 'student_id' not in session:
        return redirect('/login')

    # This filters questions so student only sees the selected DCET subject
    questions = Question.query.filter_by(subject=subject_name).all()
    
    # If no questions exist for a subject yet, we handle it gracefully
    if not questions:
        return "<h3>No questions added for " + subject_name + " yet.</h3>"

    return render_template('test.html', questions=questions, subject=subject_name)

@student.route('/student_logout')
def student_logout():
    session.clear()
    return redirect('/login')


@student.route('/subject/<int:subject_id>/materials')
def student_materials(subject_id):

    subject = Subject.query.get_or_404(subject_id)

    materials = Material.query.filter_by(subject_id=subject.id).all()

    print(materials)   # 👈 ADD THIS LINE

    return render_template(
        'student_subject.html',
        materials=materials,
        subject=subject
    )

@student.route('/student/branch/<branch_name>')
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




@student.route('/student/subject/<int:subject_id>')
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

@student.route('/student/dcet/<int:material_id>')
def student_dcet(material_id):
    if 'student_id' not in session:
        return redirect('/login')

    material = DCETMaterial.query.get_or_404(material_id)
    return render_template('student_dcet.html', material=material)


@student.route('/student/test/<subject_slug>', methods=['GET', 'POST'])
def student_test(subject_slug):

    # Convert slug to actual subject name (simple formatting)
    subject = subject_slug.replace("_", " ").title()


    # Fetch 30 questions
    questions = MCQ.query.filter_by(subject=subject).limit(30).all()

    
    if request.method == 'POST':
        score = 0
        for q in questions:
            selected = request.form.get(str(q.id))
            #if selected == q.correct:
        score += 1

        result = TestResult(
            student_name=session.get('student_name', 'Student Name'),
            subject=subject,
            score=score,
            total=len(questions),
            date_taken=datetime.now()
        )
        db.session.add(result)
        db.session.commit()

        return render_template(
            'results.html',
            score=score,
            total=len(questions),
            subject=subject,
            student_name=session.get('student_name', 'Student Name'),
            test_date=datetime.now().strftime("%d %B %Y"),
            instructor_name="Sahana"
        )

    return render_template('test.html', questions=questions, subject=subject)