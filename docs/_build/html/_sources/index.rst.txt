

Deep-Framework
==============

Introduction
------------


The DEEP-Framework is a Python-based distributed and scalable framework
for analyzing a real-time video stream. At its core, the framework
provides a modular Docker-based pipeline that allows to distribute and
parallelize all tasks from video capturing, to object detection, to
information extraction, to results collection, to output streaming.
The current version includes an implementation of following pipelines:

* A face detector and various algorithms that extract information from faces like:  

  - Age estimation
  - Gender estimation
  - Face recognition
  - Glasses detection
  - Yaw estimation
  - Pitch estimation

* A person detector and an algorithm that extract information about clothing.
* A vehicle detector and an algorithm that performs a flux analysis of the scene.

It's possible to run multiple pipeline at the same time.

A demo web app is also included.

Content Index
-------------

.. toctree::
   :maxdepth: 3
   :includehidden:

   features
   architecture
   start
   run
   usage



License
-------

This project is licensed under the GPL3 License - see the `LICENSE <https://github.com/crs4/deep_framework/blob/master/LICENSE>`__ file for details.
