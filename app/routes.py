from flask import render_template, flash, redirect, request, url_for
from flask_login import current_user, login_user, logout_user, login_required

from app import app
from app.forms import LoginForm
from app.models import User


@app.route('/')
def index():
    return render_template('index.html', title='Home')


@app.route('/user/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get(user_id)
    posts = user.get_posts(limit=5, order_by_time=True)
    return render_template('user.html', title='User', user=user, posts=posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Если пользователь входил ранее
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    
    # Проверка корректности данных, если метод POST
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        # Проверка введённых
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    
    return render_template('login.html', title='Sing In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))
