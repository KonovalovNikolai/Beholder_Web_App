import base64
import binascii

from flask import abort, flash, jsonify, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app import app, db
from app.forms import ChangePasswordForm, EditProfileForm, LoginForm
from app.models import Avatar, User


@app.route('/avatar/<path:filename>')
def avatar(filename):
    return send_from_directory(app.config["AVATARS_PATH"], filename, as_attachment=True)


@app.route('/')
def index():
    return render_template('index.html', title='Home')


@app.route('/api/upload_avatar/<int:user_id>', methods=['POST'])
def upload_avatar(user_id):
    if current_user.is_anonymous:
        return jsonify(status='Ok', result='Error')

    user = User.query.get(user_id)
    if not user or not current_user.is_can_edit(user):
        return jsonify(status='Ok', result='Error')

    image = None
    if request.method == 'POST' and 'blob' in request.form:
        image = request.form.get('blob')
        if not image:
            return jsonify(status='Ok', result='Error')

    print(image[:23])
    image = image[22:]
    filename = f'{user_id}.png'
    path = f'./app/{app.config["AVATARS_PATH"]}{filename}'

    with open(path, 'wb') as f:
        try:
            f.write(base64.b64decode(image))
        except binascii.Error:
            return jsonify(status='Ok', result='Error')

    user.set_avatar(filename)
    db.session.commit()

    return jsonify(status='Ok', result='Done')


@app.route('/user/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get(user_id)

    if not user:
        abort(404)

    posts = user.get_posts(limit=5, order_by_time=True)
    return render_template('user.html', title='User', user=user, posts=posts)


@app.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_profile(user_id):
    user = User.query.get(user_id)

    if not user:
        abort(404)

    # Проверка прав пользователя
    if not current_user.is_can_edit(user):
        abort(403)

    profile_form = EditProfileForm()
    password_form = ChangePasswordForm()

    # Обработка формы изменения личной информации
    if profile_form.form_name in request.form and profile_form.validate_on_submit():
        user.update_from_form(profile_form)
        db.session.commit()
        return redirect(url_for('edit_profile', user_id=user_id))

    # Обработка формы изменения пароля
    if password_form.form_name in request.form and password_form.validate_on_submit():
        # Проверка совпадения старого пароля
        if user.check_password(password_form.old_password):
            flash('Неверно введён пароль')
            return redirect(url_for('edit_profile', user_id=user_id))
        user.set_password(password_form.new_password)
        flash('Пароль был изменён')
        return redirect(url_for('edit_profile', user_id=user_id))

    user.fill_form(profile_form)

    return render_template('edit_profile.html', title='Edit profile', user=user,
                           profile_form=profile_form, password_form=password_form)


@app.route('/user/<int:user_id>/posts')
@login_required
def user_posts(user_id):
    user = User.query.get(user_id)

    if not user:
        abort(404)

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
            flash('Неверная почта или пароль.')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))

    return render_template('login.html', title='Вход', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/moderation')
@login_required
def moderation():
    if not current_user.is_moderator():
        abort(403)

    avatar_page = request.args.get('page', 1, type=int)
    avatars = db.session.query(Avatar).filter(Avatar.is_proved == 0).paginate(avatar_page, 10, True)
    next_url = url_for("moderation", page=avatars.next_num) if avatars.has_next else None
    prev_url = url_for("moderation", page=avatars.prev_num) if avatars.has_prev else None

    return render_template('moderation.html', title='Модерация', avatars=avatars.items, next_url=next_url,
                           prev_url=prev_url)
