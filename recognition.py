from threading import Lock
import face_recognition

from app.models import Student, User, Avatar, Post


class FaceRecognition:

    def __init__(self):
        self.mutex = Lock()

        self.known_faces_encodings = []
        self.students_id = []

        self.__load_students()

    def create_new_vector(self, avatar: Avatar):
        student = avatar.user.get_student()
        if not student:
            return False

        photo = avatar.get_path()

        loaded_image = face_recognition.load_image_file(photo)
        encoding = face_recognition.face_encodings(loaded_image)
        if len(encoding) != 1:
            return False

        student.set_vector(encoding[0])

        self.mutex.acquire()
        self.known_faces_encodings.append(encoding[0])
        self.students_id.append(student.id)
        self.mutex.release()

        return True

    def recognize(self, post: Post):
        ...

    def __load_students(self):
        students = Student.query.filter(Student.vector.isnot(None)).all()

        for student in students:
            self.known_faces_encodings.append(student.vector)
            self.students_id.append(student.id)
