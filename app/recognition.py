from multiprocessing import Lock
import face_recognition
import numpy as np
import copy


class FaceRecognition:

    def __init__(self, known_faces_encodings, students_id):
        self.mutex = Lock()

        self.known_faces_encodings = known_faces_encodings
        self.students_id = students_id

    def create_new_vector(self, image_path, student_id):
        loaded_image = face_recognition.load_image_file(image_path)
        encoding = face_recognition.face_encodings(loaded_image)
        if len(encoding) != 1:
            raise ValueError()

        try:
            index = self.students_id.index(student_id)
        except ValueError:
            index = None

        self.__add_vector(student_id=student_id, vector=encoding[0], index=index)

        return encoding[0]

    def recognize_v2(self, images_path):
        temp_known_faces_encodings = copy.deepcopy(self.known_faces_encodings)
        temp_students_id = copy.deepcopy(self.students_id)

        # Отмеченные студенты
        recognized = {}

        for image_path in images_path:
            # Загрузка изображения
            loaded_image = face_recognition.load_image_file(image_path)
            # Считывание дескрипторов на изображении
            face_encodings = face_recognition.face_encodings(loaded_image)

            for face_encoding in face_encodings:
                # Поиск совпадений считанного дескриптора в БД
                result = self.__search(face_encoding, temp_known_faces_encodings)

                if result:
                    index, distance = result
                    student_id = temp_students_id[index]

                    if student_id not in recognized:
                        recognized[student_id] = distance
                        continue

                    if distance < recognized[student_id]:
                        recognized[student_id] = distance

        return recognized

    def __add_vector(self, vector, student_id, index=None):
        self.__change(action=0, vector=vector, student_id=student_id, index=index)

    def delete_vector(self, student_id):
        index = self.students_id.index(student_id)

        self.__change(action=0, student_id=student_id, index=index)

    def __change(self, action, student_id, vector=None, index=None):
        self.mutex.acquire()
        if action == 0:
            if index:
                self.known_faces_encodings[index] = vector
                self.students_id[index] = student_id
            self.known_faces_encodings.append(vector)
            self.students_id.append(student_id)
        else:
            del self.students_id[index]
            del self.known_faces_encodings[index]
        self.mutex.release()

    def __search(self, face_to_compare, known_faces_encodings):
        for i, faces_encoding in enumerate(known_faces_encodings):
            distance = np.linalg.norm(faces_encoding - face_to_compare)
            if distance <= 0.6:
                return i, distance
        return None
