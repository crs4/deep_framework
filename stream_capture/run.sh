docker stop stream_capture_local
docker rm stream_capture_local

docker build . -t stream_capture:standalone

docker volume rm deep_media_volume

docker volume create --name deep_media_volume \
    --opt type=none \
    --opt device=<PATH_TO_FOLDER_WITH_MEDIA> \
    --opt o=bind

docker run  --rm --name stream_capture_local \
            --mount type=volume,source=deep_media_volume,destination=/mnt/remote_media \
            -e HP_SERVER=<SERVER_IP> \
            -e SERVER_PORT=8000 \
            -e STREAM_CAPTURE_ID=video_repo \
            -e SOURCE_video_repo=/mnt/remote_media/<VIDEO_FILE_NAME> \
            [-e REMOTE_PEER_TYPE=stream_manager] \
            stream_capture:standalone