
FROM python:3.7-slim


RUN apt-get update && apt-get install -y \ 
    build-essential \
    libjpeg-dev \
    libopencv-dev \
    pkg-config \
    iputils-ping \
    python-setuptools

RUN pip3 install \
    opencv-python==4.1.0.25 \
    pyzmq==18.0.1

COPY . /home/deepframework/collector
COPY --from=utils:deep /home/deepframework/utils /home/deepframework/collector/utils

WORKDIR /home/deepframework/collector

CMD python collector.py