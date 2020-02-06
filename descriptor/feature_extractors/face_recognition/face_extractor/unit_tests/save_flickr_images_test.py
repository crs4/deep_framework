import os
import shutil
import sys
import unittest
sys.path.append('..')
from save_flickr_images import save_flickr_images


class TestSaveFlickrImages(unittest.TestCase):
    """
    Execute unit tests on save_flickr_images module
    """

    def test_save_flickr_images(self):

        # Get current working directory
        cwd = os.path.dirname(os.path.abspath(__file__))

        # Directories for images and URLs
        images_path = os.path.join(cwd, 'images')
        urls_path = os.path.join(cwd, 'urls')

        tags = ['Sardinia']
        save_flickr_images(images_path, urls_path, tags, max_number=10)

        # Count number of downloaded images
        images_nr = 0
        for im in os.listdir(images_path):
            images_nr += 1
        self.assertLessEqual(images_nr, 10)

        # Count number of saved URLs
        with open(urls_path, 'r') as stream:
            lines = stream.readlines()
        urls_nr = len(lines)
        self.assertEquals(urls_nr, images_nr)

        # Delete files
        shutil.rmtree(images_path)
        os.remove(urls_path)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSaveFlickrImages)
    unittest.TextTestRunner(verbosity=2).run(suite)
