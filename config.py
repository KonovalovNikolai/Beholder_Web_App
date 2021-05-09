import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY") or "28e29edcfbb94deca66793fdbd0ec36b"
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123789qzectb@localhost/beholder'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SEND_FILE_MAX_AGE_DEFAULT = 0

    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

    AVATARS_PATH = 'non_static/avatars/'
    DEFAULT_AVATAR = 'default.png'
    POST_IMG_PATH = 'img/post_img/'

    UPLOAD_EXTENSIONS = ['.jpg', '.png']
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024

    EXCEL_FILES_PATH = 'non_static/excel_files/'

    POSTS_PER_PAGE = 10
