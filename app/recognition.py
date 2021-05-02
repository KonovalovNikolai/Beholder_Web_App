from threading import Lock
import face_recognition
import numpy as np

from app.models import Student, User, Avatar, Post, Journal
from app import db


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

    def recognize_v1(self, post_id):
        post = Post.query.get(post_id)
        images = post.get_images()
        images_path = [image.get_path() for image in images]

        recognited = []

        for image_path in images_path:
            loaded_image = face_recognition.load_image_file(image_path)

            # face_locations = face_recognition.face_locations(loaded_image)
            face_encodings = face_recognition.face_encodings(loaded_image)

            for face_encoding in face_encodings:
                face_distance = face_recognition.face_distance(self.known_faces_encodings, face_encoding)
                matches = list(face_distance <= 0.6)

                if True in matches:
                    first_match = matches.index(True)
                    student_id = self.students_id[first_match]
                    if student_id not in recognited:
                        tolerance = face_distance[first_match]

                        recognited.append(student_id)
                        student = Student.query.get(student_id)
                        journal = Journal(post=post, student=student, distance=tolerance)
                        db.session.add(journal)
                    continue

        post.is_done = 1
        db.session.commit()

    def recognize_v2(self, post_id):
        post = Post.query.get(post_id)
        images = post.get_images()
        images_path = [image.get_path() for image in images]

        recognized = []

        for image_path in images_path:
            loaded_image = face_recognition.load_image_file(image_path)

            face_encodings = face_recognition.face_encodings(loaded_image)

            for face_encoding in face_encodings:
                index = self.__search(face_encoding)

                if index:
                    index, distance = index
                    student_id = self.students_id[index]
                    if student_id not in recognized:
                        tolerance = distance

                        recognized.append(student_id)
                        student = Student.query.get(student_id)
                        journal = Journal(post=post, student=student, distance=tolerance)
                        db.session.add(journal)

        post.is_done = 1
        db.session.commit()

    def __search(self, face_to_compare):
        for i, known_faces_encoding in enumerate(self.known_faces_encodings):
            distance = np.linalg.norm(known_faces_encoding - face_to_compare)
            if distance <= 0.6:
                return i, distance
        return None

    def __load_students(self):
        students = Student.query.filter(Student.vector.isnot(None)).all()

        for student in students:
            print()
            self.known_faces_encodings.append(student.get_vector())
            self.students_id.append(student.id)
