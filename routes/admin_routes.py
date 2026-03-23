import datetime
import os

from flask import Blueprint, render_template, request, redirect, session, url_for
from werkzeug.utils import secure_filename

from extensions import db                     # database object
from models import Branch, DailyTarget, Subject, Material, DCETMaterial, MCQResult


admin = Blueprint('admin', __name__)


@admin.route('/dashboard', methods=['GET', 'POST'])   # ✅ FIXED (removed /admin)
def dashboard():

    if 'admin_id' not in session:
        return redirect('/login')

    # -------- POST --------
    if request.method == 'POST':
        branch_name = request.form.get('branch')
        subject_name = request.form.get('subject')
        branch_id = request.form.get('branch_id')

        if branch_name:
            if not Branch.query.filter_by(name=branch_name).first():
                db.session.add(Branch(name=branch_name))
                db.session.commit()

        if subject_name and branch_id:
            try:
                db.session.add(Subject(
                    name=subject_name,
                    branch_id=int(branch_id)
                ))
                db.session.commit()
            except:
                db.session.rollback()

    # -------- DATA --------
    branches = Branch.query.all()

    for branch in branches:
        branch.subjects = Subject.query.filter_by(branch_id=branch.id).all()

    subjects = Subject.query.all()

    mcq_results = MCQResult.query.order_by(
        MCQResult.attended_on.desc()
    ).all()

    total_attended = len(mcq_results)

    return render_template(
        'admin_dashboard.html',
        branches=branches,
        subjects=subjects,
        mcq_results=mcq_results,
        total_attended=total_attended
    )


@admin.route('/test')
def test():
    return "Admin Blueprint Working"

@admin.route('/admin/subject/<int:subject_id>/add-material', methods=['GET', 'POST'])
def admin_add_material(subject_id):
    subject = Subject.query.get_or_404(subject_id)

    if request.method == 'POST':
        title = request.form['title']
        question = request.form['question']
        answer = request.form.get('answer')

        file = request.files.get('qp_file')
        filename = None

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

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


@admin.route('/admin/edit-branch/<int:branch_id>', methods=['GET', 'POST'])
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


@admin.route('/delete-branch/<int:branch_id>', methods=['POST'])
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


@admin.route('/delete-subject/<int:subject_id>', methods=['POST'])
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
    return render_template('admin_add_dcet.html', subject=subject)


@admin.route('/subject/<int:subject_id>/materials')
def admin_subject_materials(subject_id):
    if 'admin_id' not in session:
        return redirect('/login')

    subject = Subject.query.get_or_404(subject_id)
    materials = DCETMaterial.query.filter_by(subject_id=subject_id).all()

    return render_template('admin_subject_materials.html', 
                           subject=subject,
                           materials=materials)



@admin.route('/add-dcet/<int:subject_id>', methods=['GET', 'POST'])
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

            filename = qp_file.filename
            file_path = os.path.join('static', 'uploads', filename)
            qp_file.save(file_path)

        new_material = DCETMaterial(
            subject_id=subject.id,
            title=title,
            question=question,
            answer=answer,
            qp_file=filename
        )

        db.session.add(new_material)
        db.session.commit()

        return redirect(url_for('admin.admin_subject_materials', subject_id=subject.id))

    # ✅ THIS LINE WAS MISSING
    return render_template('admin_add_dcet.html', subject=subject)
    

@admin.route('/delete-dcet/<int:material_id>', methods=['POST'])
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


# ---------------- ADMIN ADD TARGET ----------------
@admin.route('/add_target', methods=['GET', 'POST'])
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


@admin.route('/admin/mcq-results')
def admin_mcq_results():
    # Fetch all results, newest first
    results = MCQResult.query.order_by(MCQResult.attended_on.desc()).all()
    
    # Debugging: Print to your terminal to see if data exists
    print(f"Found {len(results)} results in database") 
    
    return render_template('admin_mcq_results.html', results=results)


@admin.route("/admin_attendance")
def admin_attendance():

    mcq_results = MCQResult.query.all()

    total_attended = len(mcq_results)

    return render_template(
        "admin_attendance.html",
        mcq_results=mcq_results,
        total_attended=total_attended
    )