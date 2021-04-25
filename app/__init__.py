from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap

from config import Config


app = Flask(__name__)
app.config.from_object(Config)

bootstrap = Bootstrap(app)

login = LoginManager(app)
login.login_view = 'login'

db = SQLAlchemy(app)
migrate = Migrate(app, db)


from recognition import FaceRecognition
recognition = FaceRecognition()


from app import routes, models
