

Getting Started
---------------

Hardware requirements for a GPU node
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  CPU Intel® Core™ i7 CPU @ 2.7GHz
-  GPU Nvidia with Pascal microarchitecture. Recommended feature: 3584
   CUDA core, 12 GBs GPU GDDR5X e 480 GB/s (examples: TITAN X, GeForce
   GTX 1080 Ti);
-  16 GB RAM;

Hardware requirements for a CPU node
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  CPU Intel® Core™ i7 CPU @ 2.7GHz
-  16 GB RAM;

Software requirements
~~~~~~~~~~~~~~~~~~~~~~

Operating system:

* Ubuntu 16.04 <= version <= 18.04
* macOS version >= 10.12 Sierra (**ONLY FOR A SINGLE NODE CLUSTER IN CPU MODE**)

Software:

* python 3.7
* pip 3 
* git LFS
* nvidia-driver >= 384.130
* Docker 18.03.1-ce 
* Docker Compose 1.23.1
* nvidia-docker 2 (2.0.3+docker18.03.1-1)
* nvidia-container-runtime 2 (2.0.0+docker18.03.1-1)

These softwares must be installed on each node of the cluster.

Installing
~~~~~~~~~~

Deep-Framework can be deployed on a single node cluster or in a multi
node cluster. Make sure every node is accessible via SSH. Before
installation check disk space usage stats of your Docker installation.
Deep Framework required al least 60 GB of free space on your disk.

Software dependencies:

#. Install python 3 (at least 3.7 version). 
#. Install pip3. 
#. Install `git LFS <https://github.com/git-lfs/git-lfs/wiki/Installation>`__.
#. Install nvidia-driver (at least 384.130 version).
#. Install `Docker <https://docs.docker.com/install/linux/docker-ce/ubuntu/>`__ (at least 18.03.1-ce version but lower than 19 version).
#. Install `Docker Compose <https://docs.docker.com/compose/install/>`__ (at least 1.23.1 version). 
#. Install `nvidia-docker 2 and nvidia-container-runtime2 <https://github.com/nvidia/nvidia-docker/wiki/Installation-(version-2.0)>`__ (follow instructions in order to install the proper version according to Docker's one). 
#. Clone the repository.
#. Install software dependencies with the following command: ``$ pip3 install -r requirements.txt``.
#. In order to setup Face Recognition algorithm, follow these instructions :ref:`face_recog_label`.

Deep-Framework can be deployed on a single node cluster or in a multi node cluster. Make sure every node is accessible via SSH.