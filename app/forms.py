from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    email = StringField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class LoginForm(FlaskForm):
    email = StringField('Email')
    firstname = StringField('Имя')
    lastname = StringField('Фамилия')
    patronymic = StringField('Отчетсво')

    old_password = StringField('Старый пароль')
    new_password = StringField('Новый парольп')
