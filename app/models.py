from datetime import datetime
import arrow
import numpy as np
import json

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import app, db, login
from app.forms import EditProfileForm


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(UserMixin, db.Model):
    """
    Модель пользователя.

    id: int - первичный ключ (при создании объекта назначается сам!).
    email: str - почта пользователя. Обязательно при создании объекта. Также используется для входа на сайт.
    user_type: int - код роли пользователя. (1 - студент, 2 - препод, 3 - модер) (требует изменения).
    firstname: str - имя пользователя.
    lastname: str - фамилия пользователя.
    patronymic: str - отчество поользователя.
    password_hash: str - хэш пароля пользователя. Устанавливается через метод set_password.

    student - объект студента данного пользователя. Связь one-2-one. Лучше получать через метод get_student.
    photo - объект фотографии пользователя. Связь one-2-one.
    posts - объект запроса для получения постов. Связь one-2-many. Получать через метод get_posts.
    """

    id = db.Column(db.Integer, primary_key=True)

    user_type = db.Column(db.Integer)

    firstname = db.Column(db.String(64))
    lastname = db.Column(db.String(64))
    patronymic = db.Column(db.String(64))

    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    student = db.relationship('Student', backref=db.backref('user', uselist=False))
    avatar = db.relationship('Avatar', backref=db.backref('user', uselist=False))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    requests = db.relationship('Request', backref='user', lazy='dynamic')

    def set_password(self, password: str):
        """
        Установить пароль пользователю.
        Пароль будет захэширован, а его оригинал станет неизвестен.
            password: str - задаваемый пароль.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """
        Сравнить хеш пароля пользователя и хэш введённой строки.
        Возвращает True, если хэши совпали. Иначе False.
            password: str - строка для сравнения.
        """
        return check_password_hash(self.password_hash, password)

    def get_fullname(self):
        """
        Сформировать ФИО пользователя.
        Если одно из полей ФИО не указано, оно пропускается.
        Если ни одно из полей не задано, то вернёт указанный email вместо ФИО.
        """
        name = ''

        if self.lastname and self.firstname and self.patronymic:
            name = '{} {} {}'.format(self.lastname, self.firstname, self.patronymic)
        elif self.lastname and self.firstname:
            name = '{} {}'.format(self.lastname, self.firstname)
        elif self.firstname and self.patronymic:
            name = '{} {}'.format(self.firstname, self.patronymic)
        elif self.firstname:
            name = self.firstname

        if name == '':
            return self.email
        return name

    def get_role(self):
        """
        Получить название роли пользователя, в зависимости от его типа.
        Соответствие типов:
            1 - Студент;
            2 - Преподаватель;
            3 - Модератор.
        """
        if self.is_student():
            return 'Студент'
        if self.is_lecture():
            return 'Сотрудник'
        return 'Модератор'

    def get_posts(self, limit=None, order_by_time=False, get_all=True):
        """
        Получить сделанные/связанные посты пользователя.
        Если пользователь студент, то возвращенны будут записи, на которых он был отмечен.
        Иначе будут возвращены сделанные пользователем записи.
        Аргументы:
            limit=None - ограничить количество получаемых записей. Если None, то не применяется.
            order_by_time=False - отсортировать записи по времени. Если False, то не применяется.
            get_all=True - Если True, то записи будут возвращены в виде массива.
                Если False, то вернётся сам объект запроса.
        """

        if self.is_student():
            student = self.get_student()
            posts = student.get_visits(limit, order_by_time, get_all)
            return posts

        posts = self.posts.filter(Post.is_done.isnot(0))
        if order_by_time:
            posts = posts.order_by(db.desc(Post.timestamp))
        if limit:
            posts = posts.limit(limit)
        if get_all:
            posts = posts.all()
        return posts

    def check_request(self, post_id: int):
        res = self.requests.filter(Request.post_id == post_id).all()
        if res:
            return True
        return False

    def get_avatar(self):
        """
        Получить соответсвующий пользователю объект фото.
        Если объект не существует, возвращает None.
        """
        if not self.avatar:
            return None
        return self.avatar[0]

    def set_avatar(self, filename: str):
        """
        Установить пользователю фото.
        """
        avatar = self.get_avatar()
        if not avatar:
            avatar = Avatar(user=self)
            db.session.add(avatar)
            avatar.set(filename)
            return
        avatar.set(filename)

    def get_avatar_name(self, check_is_proved=True):
        """
        Получить путь к фотографии пользователя.
        Если у пользователя нет фото, вернётся путь к стандартной иконке.
        Если пользователь студент и его фото не проверенно, то вернётся стандартная иконка.
        """
        avatar = self.get_avatar()
        if not avatar:
            return app.config['DEFAULT_AVATAR']
        if check_is_proved and avatar.is_proved == 0:
            return app.config['DEFAULT_AVATAR']
        return avatar.filename

    def get_avatar_path(self):
        avatar = self.get_avatar()
        if not avatar:
            return None
        return avatar.get_path()

    def delete_avatar(self):
        avatar = self.get_avatar()
        if avatar:
            db.session.delete(avatar)

    def get_student(self):
        """
        Получить соответсвующий пользователю объект студента.
        Если пользователь не студент - возвращает None.
        Если также сама создаст объект, если он не был создан раньше.
        """
        if not self.is_student():
            return None
        if not self.student:
            self._make_student()
        return self.student[0]

    def is_student(self):
        if self.user_type == 1:
            return True
        return False

    def is_lecture(self):
        if self.user_type == 2:
            return True
        return False

    def is_moderator(self):
        if self.user_type == 3:
            return True
        return False

    def fill_form(self, form: EditProfileForm):
        form.email.data = self.email
        form.firstname.data = self.firstname
        form.lastname.data = self.lastname
        form.patronymic.data = self.patronymic

    def update_from_form(self, form: EditProfileForm):
        self.email = form.email.data
        self.firstname = form.firstname.data
        self.lastname = form.lastname.data
        self.patronymic = form.patronymic.data

    def is_can_edit(self, obj) -> bool:
        if isinstance(obj, User):
            if self != obj and not self.is_moderator():
                return False
            return True

        if isinstance(obj, Post):
            if self.is_moderator() or obj.author == self:
                return True
            return False

    def _make_student(self):
        """
        Создать объект студента для данного пользователя.
        """
        if self.user_type != 1:
            return
        s = Student(user=self)
        db.session.add(s)
        db.session.commit()

    def __repr__(self):
        return '<User {}>'.format(self.get_fullname())


class Avatar(db.Model):
    """
    Модель аватара пользователя.
    id: int - первичный ключ (при создании объекта назначается сам!).
    user_id: int - id пользователя (назначается сам!).
    filename: str - название файла. Обязательно при создании!
    is_proved: int - фото проверенно модератором.

    user - объект пользователя, которому принадлежит фото. Обязательно при создании!
    """
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    filename = db.Column(db.String(64), index=True, unique=True)
    is_proved = db.Column(db.Integer)

    def set(self, filename: str):
        self.filename = filename
        if self.user.is_student():
            self.is_proved = 0
        else:
            self.is_proved = 1

    def get_filename(self, ):
        return self.filename

    def get_path(self):
        return '{}{}{}'.format('./app/', app.config["AVATARS_PATH"], self.filename)

    def prove(self):
        self.is_proved = 1


class Post(db.Model):
    """
    Модель записи.

    id: int - первичный ключ (при создании объекта назначается сам!).
    user_id: int - id автора поста (назначается сам!).
    room: str - аудитория.
    lesson: str - пара.
    notes: str - заметки о записи от автора.
    timestamp: datetime - время создание записи (назначается сама!).

    author - ссылка на объект пользователя, создавшего пост. Обязательно при создании!
    photos - объект запроса, для получения связанных с записью фото.
    journals - объект запроса, для получения отмеченных студентов.
    """
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    room = db.Column(db.String(140))
    lesson = db.Column(db.String(140))
    notes = db.Column(db.Text())
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    is_done = db.Column(db.Integer)
    changed = db.Column(db.Integer, default=1)
    excel_file_name = db.Column(db.String(64))

    images = db.relationship('Image', backref='post', lazy='dynamic')
    journals = db.relationship('Journal', backref='post', lazy='dynamic')
    requests = db.relationship('Request', backref='post', lazy='dynamic')

    images_number = 0

    def get_images(self, get_all=True):
        if get_all:
            images = self.images.all()
            self.images_number = len(images)
            return images
        return self.images

    def get_humanized_time(self):
        time = arrow.get(self.timestamp)
        return time.humanize(locale='ru')

    def get_excel_path(self):
        if not self.excel_file_name:
            return None
        return "./app/" + app.config['EXCEL_FILES_PATH'] + self.excel_file_name

    def get_first_image(self):
        return self.images.first()

    def get_visitors(self):
        return self.journals.all()

    def get_requests(self):
        return self.requests.order_by(db.desc(Request.timestamp)).all()

    def check_student(self, student_id: int):
        res = self.journals.filter(Journal.student_id == student_id).first()
        if res:
            return True
        return False

class Journal(db.Model):
    """
    Модель отметок посещений для записи.

    id: int - первичный ключ (при создании объекта назначается сам!).
    student_id: int - id отмеченного студента (назначается сам!).
    post_id: int - id записи (назначается сам!).
    distance: int - расстояние между векторами определяющие студента.
    lecturer_proved: int - присутствие потвержденно препадом.
    student_proved: int - студент потвердил присутствие.

    post - объект записи, к которой относится отметка. Обязательно при создании!
    student - объект отмеченного студента. Обязательно при создании!
    """
    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    distance = db.Column(db.Integer)
    lecturer_proved = db.Column(db.Integer, default=0)
    student_proved = db.Column(db.Integer, default=0)

    def get_distance(self, digits=3):
        if not self.distance:
            return '-'
        return f'{self.distance:.{digits}f}'


class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

    def get_humanized_time(self):
        time = arrow.get(self.timestamp)
        return time.humanize(locale='ru')


class Image(db.Model):
    """
    Модель фотографий из записей.
    id: int - первичный ключ (при создании объекта назначается сам!).
    post_id: int - id записи (назначается сам!).
    filename: str - название файла. Обязательно при создании!

    post - объект записи, к которой относится фото. Обязательно при создании!
    """
    id = db.Column(db.Integer, primary_key=True)

    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    filename = db.Column(db.String(64))

    def get_path(self, to_static=False):
        path = ''
        if not to_static:
            path = './app/static/'
        return '{}{}{}'.format(path, app.config['POST_IMG_PATH'], self.filename)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    vector = db.Column(db.Text())

    visits = db.relationship('Journal', backref='student', lazy='dynamic')

    def get_visits(self, limit=None, order_by_time=False, get_all=True):
        posts = db.session.query(Post).join(Journal).filter(Journal.student_id == self.id)
        if order_by_time:
            posts = posts.order_by(db.desc(Post.timestamp))
        if limit:
            posts = posts.limit(limit)
        if get_all:
            posts = posts.all()
        return posts

    def get_vector(self):
        return np.array(json.loads(self.vector))

    def set_vector(self, array):
        data = json.dumps(array.tolist())
        self.vector = data
