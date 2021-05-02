from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
# from celery import Celery

from config import Config


# def make_celery(app):
#     app = app
#     celery = Celery(
#         app.import_name,
#         backend=app.config['CELERY_BROKER_URL'],
#         broker=app.config['CELERY_RESULT_BACKEND']
#     )
#     celery.conf.update(app.config)
#
#     class ContextTask(celery.Task):
#         def __call__(self, *args, **kwargs):
#             with app.app_context():
#                 return self.run(*args, **kwargs)
#
#     celery.Task = ContextTask
#     return celery


app = Flask(__name__)
app.config.from_object(Config)

bootstrap = Bootstrap(app)

login = LoginManager(app)
login.login_view = 'login'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# celery = make_celery(app)

from app.recognition import FaceRecognition
recognition = FaceRecognition()


from app import routes, models
