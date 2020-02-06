import cv2
import os
import urllib2
from facenet_tools import FaceNet
from flickrapi import FlickrAPI
from math import ceil
from utils import save_YAML_file

FLICKR_PUBLIC = 'e84873bb7e156df487a43662557d106b'
FLICKR_SECRET = '4f11f90fba724a55'


def save_flickr_images(images_path, urls_path, tags, max_size=None, max_number=None, faces=None):
    """
    Save Flickr images with given tags

    :type images_path: string
    :param images_path: path of directory where found images will be saved

    :type urls_path: string
    :param urls_path: path of YAML files with urls to be saved

    :type tags: list
    :param tags: list of tags

    :type max_size: int
    :param max_size: maximum size in pixels for saved images

    :type max_number: int
    :param max_number: maximum number of images to be downloaded

    :type faces: int
    :param faces: number of faces that must be present in an image in order to save it
    """

    if not os.path.exists(images_path):
        os.makedirs(images_path)

    urls = {}

    # Create comma-separated list of tags
    tags_str = ''
    for tag in tags:
        if tags_str != '':
            tags_str += ','
        tags_str += tags_str + tag
    tags_mod = tags_str.replace(' ', '_')

    flickr = FlickrAPI(FLICKR_PUBLIC, FLICKR_SECRET, format='parsed-json')

    # Download only Creative-Commons images or images without known copyright restrictions
    license = '1,2,3,4,5,6,7'

    # Flickr API can return at most 500 photos per page
    per_page = 500

    results = flickr.photos.search(tags=tags_str, tag_mode='all',
                                   license=license, per_page=per_page, format='parsed-json')

    # Get number of pages
    pages = int(results['photos']['pages'])
    if pages > 1:
        print 'Number of pages: %d' % pages

    if faces is not None:
        facenet = FaceNet()

    counter = 1
    for page in range(1, pages + 1):

        results = flickr.photos.search(tags=tags_str, tag_mode='all', license=license,
                                       per_page=500, format='parsed-json', page=page)

        url = None
        for r in results['photos']['photo']:
            if r['ispublic'] == 1:
                try:
                    title = r['title']
                    author = r['owner']
                    photo = flickr.photos.getSizes(photo_id=r['id'], format='parsed-json')

                    for p in photo['sizes']['size']:
                        if p['label'] == 'Original':

                            # Limit of images reached
                            if max_number and counter > max_number:

                                # Save file with URLs
                                save_YAML_file(urls_path, urls)
                                return

                            url = p['source']
                            title = title.replace(' ', '-')
                            image = urllib2.urlopen(url).read()
                            file_name = tags_mod + '_' + str(counter)
                            ext = 'jpg'
                            file_name += '.' + ext

                            file_path = os.path.join(images_path, file_name)

                            with open(file_path, 'wb') as f:
                                f.write(image)
                                counter += 1

                            if faces is not None:

                                # Check number of detected faces in image
                                img = cv2.imread(file_path, cv2.IMREAD_COLOR)
                                det_faces = facenet.detect_faces_in_image(img)
                                if len(det_faces) != faces:
                                    os.remove(file_path)
                                    counter -= 1
                                    continue

                            if max_size is not None:

                                # Resize image in order to have a maximum size less than max_size
                                if faces is None:
                                    img = cv2.imread(file_path, cv2.IMREAD_COLOR)
                                if img is not None:
                                    (rows, cols, chs) = img.shape
                                    max_size_before = float(max(rows, cols))
                                    if max_size_before > max_size:
                                        fx = fy = 1.0 / ceil(max_size_before / max_size)
                                        img = cv2.resize(img, dsize=(0, 0), fx=fx, fy=fy)
                                        cv2.imwrite(file_path, img)
                                else:

                                    # Delete file
                                    os.remove(file_path)

                            urls[file_name] = str(url)

                except Exception as e:
                    if url is not None:
                        print "could not load: " + url
                    print e

    # Save file with URLs
    save_YAML_file(urls_path, urls)


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='Save Flickr images')
    parser.add_argument('images_path', help='path of directory where found images will be saved')
    parser.add_argument('urls_path', help='path of YAML files with urls to be saved')
    parser.add_argument('tags', help='list of tags', nargs='+')
    parser.add_argument('--max_size', '-s', help='maximum size in pixels for saved images', type=int)
    parser.add_argument('--max_number', '-n', help='maximum number of images to be downloaded', type=int)
    parser.add_argument('--faces', '-f', help='if used, number of faces that must be present '
                                              'in an image in order to save it', type=int)

    args = parser.parse_args()

    save_flickr_images(args.images_path, args.urls_path, args.tags, args.max_size, args.max_number, args.faces)
