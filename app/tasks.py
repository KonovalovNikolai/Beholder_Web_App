from app import celery, recognition, db
from app.models import Student, Post, Journal


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


