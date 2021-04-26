from app import celery, recognition


@celery.task()
def recognize_task(post_id):
    recognition.recognize(post_id)
    return post_id


