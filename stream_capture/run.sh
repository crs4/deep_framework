docker stop stream_capture_local
docker rm stream_capture_local

docker build . -t stream_capture:standalone

docker run  --rm --name stream_capture_local \
            -v /mnt/remote_media:/mnt/remote_media \
            -e HP_SERVER=<SERVER_IP> \
            -e SERVER_PORT=8000 \
            -e STREAM_CAPTURE_ID=video_repo \
            -e SOURCE_video_repo=/mnt/remote_media/<PATH_TO_VIDEO_FILE> \
            stream_capture:standalone