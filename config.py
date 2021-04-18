import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY") or "it-is-a-secret"
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    AVATARS_PATH = 'img/avatars/'
    DEFAULT_AVATAR = 'default.png'
    POST_IMG_PATH = 'img/post_img/'

    UPLOAD_EXTENSIONS = ['.jpg', '.png']
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024

    # SEND_FILE_MAX_AGE_DEFAULT = 0
