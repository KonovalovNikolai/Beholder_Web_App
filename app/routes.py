import imghdr
import uuid
import os
from flask import abort, flash, jsonify, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.utils import secure_filename

from app import app, db, recognition
from app.forms import ChangePasswordForm, EditProfileForm, LoginForm, CreatePostForm
from app.models import Avatar, User, Post, Image, Request, Journal
# from app.tasks import recognize_task


def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')


@app.errorhandler(413)
def too_large(e):
    return "File is too large", 413


@app.route('/avatar/<path:filename>')
def avatar(filename):
    return send_from_directory(app.config["AVATARS_PATH"], filename, as_attachment=True)


@app.route('/api/secure_image', methods=['POST'])
def secure_post_image():
    if current_user.is_anonymous and current_user.is_student():
        return "Доступ запрещён", 403

    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in app.config['UPLOAD_EXTENSIONS'] or \
                file_ext != validate_image(uploaded_file.stream):
            return "Некорректный формат изображения", 400
    return '', 204


@app.route('/api/upload_image', methods=['POST'])
def upload_post_image():
    if current_user.is_anonymous and current_user.is_student():
        return "Доступ запрещён", 403

    form = CreatePostForm()

    post = Post(author=current_user, lesson=form.lesson.data, room=form.room.data, notes=form.notes.data, is_done=0)
    db.session.add(post)

    for key, f in request.files.items():
        if key.startswith('file'):
            filename = secure_filename(f.filename)
            if filename != '':
                file_ext = os.path.splitext(filename)[1]
                if file_ext not in app.config['UPLOAD_EXTENSIONS'] or file_ext != validate_image(f.stream):
                    continue
                filename = '{}_{}{}'.format(current_user.id, str(uuid.uuid4()), file_ext)
                image = Image(post=post, filename=filename)
                f.save(os.path.join('app/static/' + app.config['POST_IMG_PATH'], image.filename))
                db.session.add(image)

    db.session.commit()

    # task = recognize_task.delay(post_id=post.id)
    # return jsonify(url=url_for('recognition_status', task_id=task.id)), 201
    return "Ok", 201

# @app.route('/api/task/<task_id>', methods=['GET'])
# def recognition_status(task_id):
#     if current_user.is_anonymous and current_user.is_student():
#         return "Доступ запрещён", 403
#
#     task = recognize_task.AsyncResult(task_id)
#     if task.ready():
#         post_id = task.get()
#         print(post_id)
#         return jsonify(done=True, url=url_for('post', post_id=post_id)), 201
#     return jsonify(done=False), 201


@app.route('/api/upload_avatar/<int:user_id>', methods=['POST'])
def upload_avatar(user_id):
    if current_user.is_anonymous:
        return "Доступ запрещён", 403

    user = User.query.get(user_id)
    if not user or not current_user.is_can_edit(user):
        return "Что-то пошло не так", 400

    uploaded_file = request.files['file']
    if uploaded_file != '':
        filename = str(user.id) + '.png'
        uploaded_file.save(os.path.join('app/' + app.config['AVATARS_PATH'], filename))

        user.set_avatar(filename)
        db.session.commit()

        return jsonify(result='Done'), 202

    return "Что-то пошло не так", 400


@app.route('/api/approve', methods=['POST'])
def approve_avatar():
    if current_user.is_anonymous or not current_user.is_moderator():
        return "Доступ запрещён", 403

    if 'id' not in request.form:
        return "Что-то пошло не так", 400

    avatar_id = request.form.get('id')
    avatar = Avatar.query.get(avatar_id)
    if not avatar:
        return "Что-то пошло не так", 400

    res = recognition.create_new_vector(avatar)

    if not res:
        return "Что-то пошло не так", 400

    avatar.is_proved = 1
    db.session.commit()

    return jsonify(result='Done'), 201


@app.route('/api/approve_student/<int:journal_id>', methods=['POST'])
def approve_student(journal_id):
    if current_user.is_anonymous or current_user.is_student():
        return "Доступ запрещён", 403

    if 'id' not in request.form:
        return "Ошибка", 400
    student_id = request.form.get('id', type=int)

    student = User.query.get(student_id)
    journal = Journal.query.get(journal_id)

    if journal.student_id != student.id:
        return "Что-то пошло не так", 400

    if not current_user.is_can_edit(journal.post):
        return "Что-то пошло не так", 400

    journal.lecturer_proved = 1
    db.session.commit()

    return jsonify(result='Done'), 202


@app.route('/api/send_request/<int:post_id>', methods=['POST'])
def take_request(post_id):
    if current_user.is_anonymous or not current_user.is_student():
        return "Доступ запрещён", 403

    post = Post.query.get(post_id)
    if not post:
        return "Что-то пошло не так", 400

    if post.check_student(current_user.get_student().id):
        return "Запрос уже был отправлен", 406

    request_ = Request(user=current_user, post=post)
    db.session.add(request_)
    db.session.commit()

    return jsonify(result='Done'), 202


@app.route('/api/accept_request/<int:post_id>', methods=['POST'])
def accept_request(post_id):
    if current_user.is_anonymous or current_user.is_student():
        return "Доступ запрещён", 403

    if 'id' not in request.form:
        return "Ошибка", 400
    user_id = request.form.get('id', type=int)

    post = Post.query.get(post_id)
    if not current_user.is_can_edit(post):
        return "Что-то пошло не так", 400

    request_ = Request.query.filter(Request.post_id == post_id, Request.user_id == user_id).first()
    if not request_:
        return "Что-то пошло не так", 400

    user = User.query.get(user_id)

    journal = Journal(student=user.get_student(), post=post, lecturer_proved=1)

    db.session.delete(request_)
    db.session.add(journal)
    db.session.commit()

    return jsonify(result='Done'), 202


@app.route('/api/cancel_request/<int:post_id>', methods=['POST'])
def cancel_request(post_id):
    if current_user.is_anonymous:
        return "Доступ запрещён", 403

    if 'id' not in request.form:
        return "Ошибка", 400

    user_id = request.form.get('id', type=int)
    if current_user.is_student():
        if current_user.id != user_id:
            return "Ошибка", 400

    Request.query.filter(Request.post_id == post_id, Request.user_id == user_id).delete()
    db.session.commit()

    return jsonify(result='Done'), 202


@app.route('/')
def index():
    return render_template('index.html', title='Home')


@app.route('/posts')
@login_required
def posts():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter(Post.is_done.isnot(0)).order_by(db.desc(Post.timestamp)).paginate(page, 10, True)

    next_url = url_for("posts", page=posts.next_num) if posts.has_next else None
    prev_url = url_for("posts", page=posts.prev_num) if posts.has_prev else None

    return render_template('posts.html', title='Записи', posts=posts.items, next_url=next_url, prev_url=prev_url)


@app.route('/post/<int:post_id>')
@login_required
def post(post_id):
    post = Post.query.get_or_404(post_id)

    return render_template('post.html', title='Запись', post=post)


@app.route('/new_post')
@login_required
def new_post():
    if current_user.is_student():
        abort(403)

    form = CreatePostForm()

    return render_template('new_post.html', title='Новая запись', form=form)


@app.route('/user/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)

    posts = user.get_posts(limit=5, order_by_time=True)
    return render_template('user.html', title='Профиль', user=user, posts=posts)


@app.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_profile(user_id):
    user = User.query.get_or_404(user_id)

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

    return render_template('edit_profile.html', title='Редактирование профиля', user=user,
                           profile_form=profile_form, password_form=password_form)


@app.route('/user/<int:user_id>/posts')
@login_required
def user_posts(user_id):
    user = User.query.get_or_404(user_id)

    page = request.args.get('page', 1, type=int)
    posts = user.get_posts(get_all=False).paginate(page, 10, True)
    next_url = url_for("user_posts", user_id=user.id, page=posts.next_num) if posts.has_next else None
    prev_url = url_for("user_posts", user_id=user.id, page=posts.prev_num) if posts.has_prev else None

    return render_template('user_posts.html', title='Записи пользователя', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


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
