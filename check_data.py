from app import app
from models import Student, Subject

with app.app_context():
    student = Student.query.first()
    print("Student branch_id:", student.branch_id)

    subjects = Subject.query.all()
    for s in subjects:
        print("Subject:", s.name, "Branch ID:", s.branch_id)