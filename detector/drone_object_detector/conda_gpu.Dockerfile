# Use CUDA 10.1 
FROM nvidia/cuda:10.1-cudnn7-runtime

ENV DEBIAN_FRONTEND noninteractive

# Use miniconda for managing packages
RUN apt-get -qq update && apt-get -qq -y install curl bzip2 \
    && curl -sSL https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -o /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -bfp /usr/local \
    && rm -rf /tmp/miniconda.sh \
    && conda install -y python=3.7 \
    && conda update conda \
    && apt-get -qq -y remove curl bzip2 \
    && apt-get -qq -y autoremove \
    && apt-get autoclean \
    && rm -rf /var/lib/apt/lists/* /var/log/dpkg.log \
    && conda clean --all --yes

ENV PATH /opt/conda/bin:$PATH

# Installing pytorch and other detectron2 dependencies
RUN conda install pytorch torchvision cudatoolkit=10.1 -c pytorch
RUN conda install -y -c conda-forge pycocotools opencv git IPython detectron2

# Installing detectron2 
# RUN python -m pip install detectron2 -f \
#     https://dl.fbaipublicfiles.com/detectron2/wheels/cu101/torch1.5/index.html

# Installing FCOS detector from AdelaiDet repo
RUN git clone https://github.com/aim-uofa/AdelaiDet.git /detector
WORKDIR /detector
RUN git checkout f41b5f4d7809abc76d6a3f864e693abd2112e3a7
RUN apt-get update
RUN apt-get -y install build-essential cmake ninja-build protobuf-compiler libprotobuf-dev
RUN python setup.py build develop -d ./dist

# Adding source my code and models
ADD src /detector/src/
ADD models /detector/models/

ENV DEVICE_TYPE="cuda"

WORKDIR /detector/src
CMD python frame_provider.py