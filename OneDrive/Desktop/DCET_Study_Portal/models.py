from app import db

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

class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'))

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    link = db.Column(db.String(200))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class MCQ(db.Model):
    __tablename__ = 'mcq'   # 👈 ADD THIS LINE

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(50))
    question = db.Column(db.String(500))
    opt1 = db.Column(db.String(200))
    opt2 = db.Column(db.String(200))
    opt3 = db.Column(db.String(200))
    opt4 = db.Column(db.String(200))
    correct = db.Column(db.String(100))


class Instructor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))    