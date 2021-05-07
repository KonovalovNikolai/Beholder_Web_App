import imghdr
import uuid
import os
from flask import abort, flash, jsonify, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.utils import secure_filename

from app import app, db, recognition
from app.forms import ChangePasswordForm, EditProfileForm, LoginForm, CreatePostForm
from app.models import Avatar, User, Post, Image, Request, Journal, Student

# from app.tasks import recognize_task
from app.tasks import import_to_excel


def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')


@app.errorhandler(400)
def bad_request(e):
    return "Bad request", 400


@app.errorhandler(403)
def forbidden(e):
    return "Отказано в доступе", 403


@app.errorhandler(413)
def too_large(e):
    return "Файл слишком большой", 413


@app.route('/avatar/<path:filename>')
def avatar(filename):
    return send_from_directory(app.config["AVATARS_PATH"], filename, as_attachment=True)


@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config["EXCEL_FILES_PATH"], filename)


@app.route('/api/download_excel/<int:post_id>')
def download_excel(post_id):
    if current_user.is_anonymous:
        abort(403)

    post = Post.query.get(post_id)
    if not post:
        abort(403)

    import_to_excel(post_id)

    return jsonify(url=url_for('download_file', filename=post.excel_file_name))


@app.route('/api/secure_image', methods=['POST'])
def secure_post_image():
    if current_user.is_anonymous and current_user.is_student():
        abort(403)

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
        abort(403)

    form = CreatePostForm()

    accept = {}

    for key, f in request.files.items():
        if key.startswith('file'):
            filename = secure_filename(f.filename)
            if filename != '':
                file_ext = os.path.splitext(filename)[1]
                if file_ext not in app.config['UPLOAD_EXTENSIONS'] or file_ext != validate_image(f.stream):
                    continue
                filename = '{}_{}{}'.format(current_user.id, str(uuid.uuid4()), file_ext)
                accept[filename] = f

    if len(accept) == 0:
        abort(400)

    post = Post(author=current_user, lesson=form.lesson.data, room=form.room.data, notes=form.notes.data, is_done=0)
    for filename, file in accept.items():
        image = Image(post=post, filename=filename)
        file.save(os.path.join('app/static/' + app.config['POST_IMG_PATH'], image.filename))
        db.session.add(image)
    db.session.add(post)
    db.session.commit()

    # task = recognize_task.delay(post_id=post.id)
    # return jsonify(url=url_for('recognition_status', task_id=task.id)), 201
    return "Ok", 201


# @app.route('/api/task/<task_id>', methods=['GET'])
# def recognition_status(task_id):
#     if current_user.is_anonymous and current_user.is_student():
#         return abort(403)
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
        abort(403)

    user = User.query.get(user_id)
    if not user or not current_user.is_can_edit(user):
        abort(403)

    f = request.files['file']
    filename = secure_filename(f.filename)
    if filename == '':
        abort(400)

    file_ext = os.path.splitext(filename)[1]
    if file_ext not in app.config['UPLOAD_EXTENSIONS'] or file_ext != validate_image(f.stream):
        abort(400)

    avatar = user.get_avatar()
    student = user.get_student()
    if avatar and student:
        recognition.delete_vector(student.id)

    filename = '{}{}'.format(str(user_id), file_ext)
    f.save(os.path.join('app/' + app.config['AVATARS_PATH'], filename))

    user.set_avatar(filename)
    db.session.commit()

    if user.is_student():
        flash('Фото успешно загружено и будет отображено после модерации.', 'success')
    else:
        flash('Фото успешно загружено.', 'success')

    return 'Ok', 202


@app.route('/api/approve_avatar/<int:avatar_id>', methods=['POST'])
def approve_avatar(avatar_id):
    if current_user.is_anonymous or not current_user.is_moderator():
        abort(403)

    avatar = Avatar.query.get(avatar_id)
    if not avatar:
        abort(400)

    student = avatar.user.get_student()
    if not student:
        abort(400)

    try:
        vector = recognition.create_new_vector(avatar.get_path(), student.id)
    except ValueError:
        abort(400)

    student.set_vector(vector)
    avatar.prove()
    db.session.commit()

    return 'Ok', 201


@app.route('/api/reject_avatar/<int:avatar_id>', methods=['POST'])
def reject_avatar(avatar_id):
    if current_user.is_anonymous or not current_user.is_moderator():
        abort(403)

    avatar = Avatar.query.get(avatar_id)
    if not avatar:
        abort(400)

    db.session.delete(avatar)
    db.session.commit()

    return 'Ok', 201


@app.route('/api/delete_journal/<int:journal_id>', methods=['DELETE'])
def delete_journal(journal_id):
    if current_user.is_anonymous or current_user.is_student():
        abort(403)
    journal = Journal.query.get(journal_id)

    if not journal:
        abort(400)
    if not current_user.is_can_edit(journal.post):
        abort(400)

    journal.post.changed = 0
    db.session.delete(journal)
    db.session.commit()
    return 'Ok', 202


@app.route('/api/approve_journal/<int:journal_id>', methods=['POST'])
def approve_journal(journal_id):
    if current_user.is_anonymous or current_user.is_student():
        abort(403)

    if 'id' not in request.form:
        abort(400)
    student_id = request.form.get('id', type=int)

    student = Student.query.get(student_id)
    journal = Journal.query.get(journal_id)

    if not student:
        abort(400)
    if not journal or journal.student_id != student.id:
        abort(400)
    if not current_user.is_can_edit(journal.post):
        abort(400)

    journal.post.changed = 0
    journal.lecturer_proved = 1
    db.session.commit()

    return 'Ok', 202


@app.route('/api/disapprove_journal/<int:journal_id>', methods=['POST'])
def disapprove_journal(journal_id):
    if current_user.is_anonymous or current_user.is_student():
        abort(403)

    if 'id' not in request.form:
        abort(400)
    student_id = request.form.get('id', type=int)

    student = Student.query.get(student_id)
    journal = Journal.query.get(journal_id)

    if not student:
        abort(400)
    if not journal or journal.student_id != student.id:
        abort(400)
    if not current_user.is_can_edit(journal.post):
        abort(400)

    journal.post.changed = 0
    journal.lecturer_proved = 0
    db.session.commit()

    return 'Ok', 202


@app.route('/api/send_request/<int:post_id>', methods=['POST'])
def take_request(post_id):
    if current_user.is_anonymous or not current_user.is_student():
        abort(403)

    post = Post.query.get(post_id)
    if not post:
        abort(400)

    if post.check_student(current_user.get_student().id):
        abort(406)

    request_ = Request(user=current_user, post=post)
    db.session.add(request_)
    db.session.commit()

    return 'Ok', 202


@app.route('/api/accept_request/<int:post_id>', methods=['POST'])
def accept_request(post_id):
    if current_user.is_anonymous or current_user.is_student():
        abort(403)

    if 'id' not in request.form:
        abort(400)
    user_id = request.form.get('id', type=int)

    post = Post.query.get(post_id)
    if not current_user.is_can_edit(post):
        abort(400)

    request_ = Request.query.filter(Request.post_id == post_id, Request.user_id == user_id).first()
    if not request_:
        abort(400)

    user = User.query.get(user_id)

    journal = Journal(student=user.get_student(), post=post, lecturer_proved=1)
    post.changed = 0
    db.session.delete(request_)
    db.session.add(journal)
    db.session.commit()

    return 'Ok', 202


@app.route('/api/cancel_request/<int:post_id>', methods=['POST'])
def cancel_request(post_id):
    if current_user.is_anonymous:
        abort(403)

    if 'id' not in request.form:
        abort(400)

    user_id = request.form.get('id', type=int)
    if current_user.is_student():
        if current_user.id != user_id:
            abort(400)

    Request.query.filter(Request.post_id == post_id, Request.user_id == user_id).delete()
    db.session.commit()

    return 'Ok', 202


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
        flash('Данные были изменены.', 'success')
        return redirect(url_for('edit_profile', user_id=user_id))

    # Обработка формы изменения пароля
    if password_form.form_name in request.form and password_form.validate_on_submit():
        # Проверка совпадения старого пароля
        if user.check_password(password_form.old_password):
            flash('Неверно введён пароль.', 'danger')
            return redirect(url_for('edit_profile', user_id=user_id))
        user.set_password(password_form.new_password)
        flash('Пароль был изменён.', 'success')
        return redirect(url_for('edit_profile', user_id=user_id))

    user.fill_form(profile_form)

    for field in password_form:
        if field.errors:
            return render_template('edit_profile.html', title='Редактирование профиля', user=user,
                                   profile_form=profile_form, password_form=password_form, active=True)

    return render_template('edit_profile.html', title='Редактирование профиля', user=user,
                           profile_form=profile_form, password_form=password_form, active=False)


@app.route('/user/<int:user_id>/posts')
@login_required
def user_posts(user_id):
    user = User.query.get_or_404(user_id)

    page = request.args.get('page', 1, type=int)
    posts = user.get_posts(get_all=False).paginate(page, 1, True)
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
            flash('Неверная почта или пароль.', 'danger')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)
        flash(f'Успешный вход. Добро пожаловать, {current_user.get_fullname()}!', 'success')
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
    avatars = db.session.query(Avatar).filter(Avatar.is_proved == 0).paginate(avatar_page, 1, True)
    next_url = url_for("moderation", page=avatars.next_num) if avatars.has_next else '#'
    prev_url = url_for("moderation", page=avatars.prev_num) if avatars.has_prev else '#'

    return render_template('moderation.html', title='Модерация - проверка изображений', avatars=avatars.items,
                           next_url=next_url,
                           prev_url=prev_url)
