FROM nvidia/cuda:10.1-cudnn7-devel

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get install -y \
    python3-opencv ca-certificates python3-dev git wget sudo  \
    cmake ninja-build protobuf-compiler libprotobuf-dev && \
    rm -rf /var/lib/apt/lists/*
RUN ln -sv /usr/bin/python3 /usr/bin/python

# create a non-root user
ARG USER_ID=1000
RUN useradd -m --no-log-init --system  --uid ${USER_ID} appuser -g sudo
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
USER appuser
WORKDIR /home/appuser

ENV PATH="/home/appuser/.local/bin:${PATH}"
RUN wget https://bootstrap.pypa.io/get-pip.py && \
    python3 get-pip.py --user && \
    rm get-pip.py

# install PyTorch (detector and tracker common depencency)
# See https://pytorch.org/ for other options if you use a different version of CUDA
RUN pip install --user tensorboard cython
RUN pip install --user torch==1.5+cu101 torchvision==0.6+cu101 -f https://download.pytorch.org/whl/torch_stable.html
RUN pip install --user 'git+https://github.com/cocodataset/cocoapi.git#subdirectory=PythonAPI'


RUN pip install \
	IPython \
    scipy \
    imutils==0.5.2 \
    pyzmq==18.0.1 \
    opencv-python==4.1.0.25 \
    opencv-contrib-python==4.2.0.34



# install detectron2 (detector depencency)  
RUN pip install --user 'git+https://github.com/facebookresearch/fvcore'
RUN git clone https://github.com/facebookresearch/detectron2 detectron2_repo
# set FORCE_CUDA because during `docker build` cuda is not accessible
ENV FORCE_CUDA="1"
# This will by default build detectron2 for all common cuda architectures and take a lot more time,
# because inside `docker build`, there is no way to tell which architecture will be used.
ARG TORCH_CUDA_ARCH_LIST="Kepler;Kepler+Tesla;Maxwell;Maxwell+Tegra;Pascal;Volta;Turing"
ENV TORCH_CUDA_ARCH_LIST="${TORCH_CUDA_ARCH_LIST}"

RUN pip install --user -e detectron2_repo

# Set a fixed model cache directory.
ENV FVCORE_CACHE="/tmp"

# FCOS detector installation
RUN pip install --user opencv-python IPython
RUN git clone https://github.com/aim-uofa/AdelaiDet.git
WORKDIR /home/appuser/AdelaiDet
RUN python3 setup.py build develop -d ./dist
ADD models /home/appuser/AdelaiDet/models/

# Deep sort tracker installation
RUN pip install numpy scipy opencv-python sklearn pillow vizer edict PyYAML easydict
RUN git clone https://github.com/ZQPei/deep_sort_pytorch.git ./deep_sort
RUN cp ./models/deep_sort_ckpt.t7 ./deep_sort/deep_sort/deep/checkpoint/ckpt.t7

# Copy source code
ADD src /home/appuser/AdelaiDet/src/
ENV DEVICE_TYPE="cuda"
RUN mv deep_sort/utils/ deep_sort/sort_utils/
COPY --from=utils:deep /home/deepframework/utils /detector/src/utils


WORKDIR /home/appuser/AdelaiDet/src
CMD python3 object_provider.py