from threading import Lock
import face_recognition

from app import app
from app.models import Student, User


class FaceRecognition:

    def __init__(self):
        self.mutex = Lock()

        self.known_faces_encodings = []
        self.student_id = []

        self.__load_students()

    def create_new_vector(self, user_id):
        user = User.query.get(user_id)

        student = user.get_student()
        if not student:
            return False

        photo = app.config["AVATARS_PATH"] + user.get_avatar_name(check_is_proved=False)

        loaded_image = face_recognition.load_image_file(photo)
        encoding = face_recognition.face_encodings(loaded_image)
        if len(encoding) != 1:
            return False

        student.set_vector(encoding[0])

        self.mutex.acquire()
        self.known_faces_encodings.append(encoding[0])
        self.student_id.append(student.id)
        self.mutex.release()

        return True

    def __load_students(self):
        students = Student.query.filter(Student.vector.isnot(None)).all()

        for student in students:
            self.known_faces_encodings.append(student.vector)
            self.student_id = student.id
