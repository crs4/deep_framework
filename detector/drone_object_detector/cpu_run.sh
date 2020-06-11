docker build . -f cpu.Dockerfile -t sauron_detector:cpu

docker run  --rm --name sauron_detector \
            -v /mnt/remote_media:/mnt/remote_media \
            -v /home/jsaenz/Repos/drone_object_detector/src:/detector/src/ \
            sauron_detector:cpu