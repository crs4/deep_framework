docker build . -f gpu.Dockerfile -t sauron_detector:gpu

docker run  --rm --name sauron_detector \
            -v /mnt/remote_media:/mnt/remote_media \
            -v /home/jsaenz/Repos/drone_object_detector/src:/home/appuser/AdelaiDet/src \
            sauron_detector:gpu