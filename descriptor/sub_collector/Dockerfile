
FROM python:3.7-slim


RUN apt-get update && apt-get install -y \ 
    build-essential \
    libjpeg-dev \
    libopencv-dev \
    pkg-config \
    iputils-ping \
    python-setuptools


RUN pip3 install \
    pyzmq==18.0.1 \
    opencv-python==4.1.0.25

RUN mkdir -p /home/deepframework/sub_collector

COPY . /home/deepframework/sub_collector

COPY --from=utils:deep /home/deepframework/utils/. /home/deepframework/sub_collector/utils


WORKDIR /home/deepframework/sub_collector

CMD python sub_collector.py