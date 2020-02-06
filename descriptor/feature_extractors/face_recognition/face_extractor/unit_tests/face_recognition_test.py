import cv2
import os
import unittest
import shutil
import sys

sys.path.append('..')
import face_extractor_constants as c
from face_recognition import FaceRecognition


class TestFaceModels(unittest.TestCase):
    """
    Execute software test on face_models_openface module
    """
    def test_init(self):

        data_dir_path = 'Data dir path'

        params = {c.FACE_REC_DATA_DIR_PATH_KEY: data_dir_path}

        fm = FaceRecognition(params)

        self.assertEquals(fm.data_dir_path, data_dir_path)

    def test_add_faces(self):

        # Get current working directory
        cwd = os.path.dirname(os.path.abspath(__file__))

        base_path = os.path.join(cwd, 'images', 'face_models')

        face_rec_data = os.path.abspath(os.path.join(base_path, 'face_rec_data'))

        params = {c.FACE_MODELS_MIN_DIFF_KEY: -1,
                  c.FACE_REC_DATA_DIR_PATH_KEY: face_rec_data,
                  c.FACE_REC_THRESHOLD_KEY: sys.maxint}

        fm = FaceRecognition(params)

        fm.delete_models()

        labels = [1,
                  2,
                  3,
                  4]
        tags = ['AS',
                'FC',
                'MP',
                'NC']

        image_paths = [os.path.join(base_path, 'as.jpg'),
                       os.path.join(base_path, 'fc.jpg'),
                       os.path.join(base_path, 'mp.jpg'),
                       os.path.join(base_path, 'nc.jpg')]

        fm.add_faces(labels, tags, image_paths)

        return fm

    def test_change_label_to_face(self):

        fm = self.test_add_faces()

        label = 3

        new_tag = 'PM'

        fm.change_tag_to_label(label, new_tag)

        tag = fm.get_tag(label)

        self.assertEqual(tag, 'PM')

    def test_delete_models(self):

        # Get current working directory
        cwd = os.path.dirname(os.path.abspath(__file__))

        base_path = os.path.join(cwd, 'images', 'face_models')

        face_rec_data = os.path.abspath(os.path.join(base_path, 'face_rec_data'))

        fm = self.test_add_faces()

        fm.delete_models()

        items = os.listdir(face_rec_data)

        self.assertEqual(len(items), 0)

    def test_get_labels_for_tag(self):

        fm = self.test_add_faces()

        labels = fm.get_labels_for_tag('MP')

        self.assertEqual(labels[0], 3)

    def test_get_labels(self):

        fm = self.test_add_faces()

        labels = fm.get_labels()

        self.assertEquals(len(labels), 4)

    def test_get_tag(self):

        fm = self.test_add_faces()

        tag = fm.get_tag(3)

        self.assertEqual(tag, 'MP')

    def test_get_tags(self):

        fm = self.test_add_faces()

        tags = fm.get_tags()

        self.assertEquals(len(tags), 4)

    def test_get_people_nr(self):

        fm = self.test_add_faces()

        people_nr = fm.get_people_nr()

        self.assertEqual(people_nr, 4)

    def test_recognize_face(self):

        fm = self.test_add_faces()

        # Get current working directory
        cwd = os.path.dirname(os.path.abspath(__file__))

        base_path = os.path.join(cwd, 'images', 'face_models')

        image_path = os.path.join(base_path, 'as.jpg')

        img = cv2.imread(image_path)

        (bbox, label, conf) = fm.recognize_face(img)

        self.assertEqual(label, 1)

        image_path = os.path.join(base_path, 'fc.jpg')

        img = cv2.imread(image_path)

        (bbox, label, conf) = fm.recognize_face(img)

        self.assertEqual(label, 2)

    def delete_files(self):

        # Get current working directory
        cwd = os.path.dirname(os.path.abspath(__file__))

        base_path = os.path.join(cwd, 'images', 'face_models')

        face_rec_data = os.path.abspath(os.path.join(base_path, 'face_rec_data'))

        shutil.rmtree(face_rec_data)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFaceModels)
    unittest.TextTestRunner(verbosity=2).run(suite)
