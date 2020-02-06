docker stop deep_web_server
docker rm deep_web_server

docker build . -t 156.148.14.162/server:deep_unified

docker run -p 0.0.0.0:8000:8000 \
        --name deep_web_server \
        -v $PWD/deep_app:/server/deep_app \
        -it --rm \
        156.148.14.162/server:deep_unified 