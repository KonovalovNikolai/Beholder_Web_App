from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

from app import db
from app import login


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_type = db.Column(db.Integer)
    username = db.Column(db.String(64))
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    student = db.relationship('Student', backref=db.backref('user', uselist=False), lazy='dynamic')
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    room = db.Column(db.String(140))
    lesson = db.Column(db.String(140))
    notes = db.Column(db.Text())
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    photos = db.relationship('Post_Photo', backref='post', lazy='dynamic')
    journals = db.relationship('Journal', backref='post', lazy='dynamic')


class Journal(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    distance = db.Column(db.Integer)
    lecturer_proved = db.Column(db.Integer)
    student_proved = db.Column(db.Integer)


class Post_Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    filename = db.Column(db.String(64), index=True, unique=True)


class Student_Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    filename = db.Column(db.String(64), index=True, unique=True)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    vector = db.Column(db.Text())
    is_proved = db.Column(db.Integer)

    photo = db.relationship('Student_Photo', backref=db.backref('studen', uselist=False), lazy='dynamic')
    visits = db.relationship('Journal', backref='student', lazy='dynamic')