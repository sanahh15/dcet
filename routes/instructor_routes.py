import os
from random import sample
from flask import Blueprint, render_template, request, redirect, session, flash, url_for
from werkzeug.utils import secure_filename

from extensions import db
from models import Branch, Subject, Material, StudyMaterial, MCQ, TestResult

instructor = Blueprint('instructor', __name__)

# ----- Dashboard -----
@instructor.route('/dashboard')
def dashboard():
    if 'instructor_id' not in session:
        return redirect('/login')
    return render_template('instructor_dashboard.html')

@instructor.route('/instructor/subject/<int:subject_id>/add-material', methods=['GET','POST'])
def instructor_add_material(subject_id):

    subject = Subject.query.get_or_404(subject_id)

    if request.method == 'POST':

        title = request.form.get('title')
        question = request.form.get('question')
        answer = request.form.get('answer')

        material = Material(
            title=title,
            question=question,
            answer=answer,
            subject_id=subject.id
        )

        db.session.add(material)
        db.session.commit()
        print("Saved:", title, "Subject ID:", subject.id)

        print("Instructor material saved for subject:", subject.id)

        return redirect(f'/subject/{subject.id}/materials')

    return render_template('instructor_add_material.html', subject=subject)


@instructor.route('/instructor/subjects')
def instructor_subjects():
    return render_template("instructor_subjects.html")


@instructor.route("/instructor/add-branch", methods=["POST"])
def instructor_add_branch():
    name = request.form["branch_name"]

    new_branch = Branch(name=name)
    db.session.add(new_branch)
    db.session.commit()

    return redirect("/instructor/dashboard")

@instructor.route("/instructor/add-subject", methods=["POST"])
def instructor_add_subject():
    name = request.form["subject_name"]
    branch_id = request.form["branch_id"]

    subject = Subject(name=name, branch_id=branch_id)

    db.session.add(subject)
    db.session.commit()

    return redirect("/instructor/dashboard")

@instructor.route('/instructor/logout')
def instructor_logout():
    session.pop('instructor_id', None)
    # logout should send them to the new login path as well
    return redirect('/login')



@instructor.route('/instructor/add_mcq')
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

@instructor.route('/instructor/add_mcq/<subject>', methods=['GET','POST'])
def add_mcq(subject):

    if request.method == 'POST':

        question = request.form.get('question')
        option1 = request.form.get('option1')
        option2 = request.form.get('option2')
        option3 = request.form.get('option3')
        option4 = request.form.get('option4')
        answer = request.form.get('answer')

        new_mcq = MCQ(
            subject=subject,
            question=question,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_answer=answer
        )

        db.session.add(new_mcq)
        db.session.commit()

        flash("MCQ Added Successfully")

    return render_template("instructor_add_mcq.html", subject=subject)



@instructor.route('/instructor/test_results')
def instructor_test_results():
    # Fetch all test results, newest first
    results = TestResult.query.order_by(TestResult.date_taken.desc()).all()
    return render_template('instructor_test_results.html', results=results)

@instructor.route('/instructor/generate_mcqs')
def generate_mcqs_page():
    return render_template('generate_mcqs.html')

@instructor.route('/instructor/add_study_material/<subject>', methods=['GET','POST'])
def add_study_material(subject):

    if request.method == 'POST':

        title = request.form['title']
        topic = request.form['topic']
        explanation = request.form['explanation']

        file = request.files['pdf_file']
        filename = secure_filename(file.filename)

        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        material = StudyMaterial(
            subject=subject,
            title=title,
            topic=topic,
            explanation=explanation,
            pdf_file=filename
        )

        db.session.add(material)
        db.session.commit()

    return render_template("add_study_material.html", subject=subject)

@instructor.route('/instructor/add_announcement', methods=['GET', 'POST'])
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

@instructor.route('/instructor/generate_mcqs/<subject_slug>')
def generate_mcqs(subject_slug):
    subject = subject_slugs.get(subject_slug)

    if not subject:
        return "Invalid Subject"

    # Get existing MCQs count
    existing = MCQ.query.filter_by(subject=subject).count()

    added_count = 0

    # If already 30 or more, do nothing
    if existing >= 30:
        final_count = existing
    else:
        mcq_list = sample_mcqs.get(subject, [])

        for q in mcq_list:
            new_mcq = MCQ(
                subject=subject,
                question=q['question'],
                option1=q['options'][0],
                option2=q['options'][1],
                option3=q['options'][2],
                option4=q['options'][3],
                correct=q['correct']
            )
            db.session.add(new_mcq)
            added_count += 1

        db.session.commit()
        final_count = existing + added_count

    return render_template(
        'mcq_added_confirmation.html',
        subject=subject,
        added_count=added_count,
        final_count=final_count
    )