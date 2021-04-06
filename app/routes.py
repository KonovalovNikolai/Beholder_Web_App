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


@app.route('/user/<int:user_id>/posts')
@login_required
def user_posts(user_id):
    user = User.query.get(user_id)
    page = request.args.get('page', 1, type=int)
    posts = user.get_posts(get_all=False).paginate(page, 10, True)
    next_url = url_for("user_posts", user_id=user.id, page=posts.next_num) if posts.has_next else None
    prev_url = url_for("user_posts", user_id=user.id, page=posts.prev_num) if posts.has_prev else None
    return render_template('user_posts.html', title='Ваши посты', user=user, posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


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
