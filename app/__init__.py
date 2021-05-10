from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
# from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from celery import Celery

from config import Config


def make_celery(app):
    app = app
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_BROKER_URL'],
        broker=app.config['CELERY_RESULT_BACKEND']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


app = Flask(__name__)
app.config.from_object(Config)

bootstrap = Bootstrap(app)

login = LoginManager(app)
login.login_view = 'login'
login.login_message = 'Пожалуйста, авторизуйтесь, чтобы получить доступ к этой странице.'
login.login_message_category = 'secondary'

db = SQLAlchemy(app)
db.create_all()
# migrate = Migrate(app, db)

moment = Moment(app)

celery = make_celery(app)

from app.recognition import FaceRecognition
from app.models import Student


"""
def make_recognition():
    students = Student.query.filter(Student.vector.isnot(None)).all()

    known_faces_encodings = []
    students_id = []

    for student in students:
        known_faces_encodings.append(student.get_vector())
        students_id.append(student.id)

    return FaceRecognition(known_faces_encodings, students_id)


recognition = make_recognition()
"""


from app import routes, models
