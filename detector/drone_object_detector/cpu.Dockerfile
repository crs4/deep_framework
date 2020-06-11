FROM python:3.7

RUN apt-get update -y

# gcc compiler and opencv prerequisites
RUN apt-get -y install git build-essential libglib2.0-0 libsm6 libxext6 libxrender-dev

# Detectron2 prerequisites
RUN pip install tensorboard cython
RUN pip install torch==1.5.0+cpu torchvision==0.6.0+cpu -f https://download.pytorch.org/whl/torch_stable.html
RUN pip install -U 'git+https://github.com/cocodataset/cocoapi.git#subdirectory=PythonAPI'

# Detectron2 - CPU copy
RUN python -m pip install detectron2 -f https://dl.fbaipublicfiles.com/detectron2/wheels/cpu/index.html

# RUN pip install --trusted-host pypi.python.org -r requirements.txt
# FCOS detector installation

RUN pip install \
	IPython \
    scipy \
    imutils==0.5.2 \
    pyzmq==18.0.1 \
    opencv-python==4.1.0.25 \
    opencv-contrib-python==4.2.0.34

RUN git clone https://github.com/aim-uofa/AdelaiDet.git /detector

WORKDIR /detector
RUN python setup.py build develop
ADD models /detector/models/

# Deep sort tracker installation
RUN pip install numpy scipy opencv-python sklearn pillow vizer edict PyYAML easydict
RUN git clone https://github.com/ZQPei/deep_sort_pytorch.git ./deep_sort
RUN cp ./models/deep_sort_ckpt.t7 ./deep_sort/deep_sort/deep/checkpoint/ckpt.t7

# Copy source code
ADD src /detector/src/
RUN mv deep_sort/utils/ deep_sort/sort_utils/
COPY --from=utils:deep /home/deepframework/utils /detector/src/utils


ENV DEVICE_TYPE="cpu"

WORKDIR /detector/src
CMD python object_provider.py