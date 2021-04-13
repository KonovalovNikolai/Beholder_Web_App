import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY") or "it-is-a-secret"
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    USER_PHOTO_PATH = 'img/user_photo/'
    DEFAULT_PHOTO = 'default.png'
    SEND_FILE_MAX_AGE_DEFAULT = 0
