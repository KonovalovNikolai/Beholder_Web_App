from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class LoginForm(FlaskForm):
    email = StringField('Почта', validators=[
                            DataRequired(message='Поле должно быть заполнено'),
                            Email(message='Некоректный email')])
    password = PasswordField('Пароль', validators=[DataRequired(message='Поле должно быть заполнено')])
    remember_me = BooleanField('Запомнить меня')

    submit = SubmitField('Войти')


class EditProfileForm(FlaskForm):
    form_name = 'EditProfileForm'
    email = StringField('Email', validators=[Email(message='Некоректный email')])
    firstname = StringField('Имя')
    lastname = StringField('Фамилия')
    patronymic = StringField('Отчество')


class ChangePasswordForm(FlaskForm):
    form_name = 'ChangePasswordForm'
    old_password = PasswordField('Старый пароль', validators=[DataRequired(message='Поле должно быть заполнено')])
    new_password = PasswordField('Новый пароль', validators=[
                                     DataRequired(message='Поле должно быть заполнено'),
                                     Length(min=5, message='Минимальная длина пароля %(min)d')])
    repeated_password = PasswordField('Повторите пароль', validators=[
                                          DataRequired(message='Поле должно быть заполнено'),
                                          Length(min=5, message='Минимальная длина пароля %(min)d'),
                                          EqualTo('new_password', message='Пароль не совпадают')])


class CreatePostForm(FlaskForm):
    room = StringField('Аудитория')
    lesson = StringField('Пара')
    notes = TextAreaField('Заметки')

