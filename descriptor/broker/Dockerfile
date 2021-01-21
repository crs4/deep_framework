

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
    
RUN mkdir -p /home/deepframework/broker

COPY . /home/deepframework/broker


COPY --from=utils:deep_setup /home/deepframework/utils /home/deepframework/broker/utils


WORKDIR /home/deepframework/broker

CMD python sub_broker.py