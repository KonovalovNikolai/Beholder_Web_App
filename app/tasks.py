import pandas as pd
import uuid

from app import celery, recognition, db
from app import app
from app import recognition, db
from app.models import Student, Post, Journal, User


@celery.task()
def recognize_task(post_id):
    post = Post.query.get(post_id)

    images = post.get_images()
    images_path = [image.get_path() for image in images]

    recognized = recognition.recognize_v2(images_path)

    # Отметить всех найденных студентов
    for student_id, distance in recognized.items():
        student = Student.query.get(student_id)
        journal = Journal(post=post, student=student, distance=distance)
        db.session.add(journal)

    post.is_done = 1
    db.session.commit()

    return post_id


# @celery.task()
def import_to_excel(post_id):
    post = Post.query.get(post_id)

    if post.changed == 1:
        return post.get_excel_path()

    journals = post.journals.all()

    data = {
        'ФИО': [],
        'Группа': [],
        'Дистанция': [],
        'Подтверждён': []
    }

    for journal in journals:
        data['ФИО'].append(journal.student.user.get_fullname())
        data['Группа'].append(journal.student.get_group())
        data['Дистанция'].append(journal.get_distance())
        data['Подтверждён'].append(journal.lecturer_proved)

    path = post.get_excel_path()

    if not path:
        filename = '{}.xlsx'.format(str(uuid.uuid4()))
        path = app.config['EXCEL_FILES_PATH'] + filename
        post.excel_file_name = filename

    df = pd.DataFrame(data)
    df.to_excel(path)

    post.changed = 1
    db.session.commit()

    return post_id
