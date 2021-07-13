

Features
--------

-  Can handle multiple video streams from IP cameras and webcams.
-  A frame-skipping policy which ensures a real-time behavior by always processing the latest available frame
-  Algorithms execution can be distributed across multiple nodes in a cluster.
-  Can create multiple worker for every algorithm.
-  Every algorithm can be executed in CPU and GPU modes.
-  Results and performance stats available via a `Server-Sent Event (SSE) <https://en.wikipedia.org/wiki/Server-sent_events>`__ API.
-  Can stream resulting data and input video to any web application via `WebRTC <https://en.wikipedia.org/wiki/WebRTC>`__. It can also handle the video stream provided by a client web app via WebRTC.
-  It's possibile to develop and deploy your own detector. See :ref:`detector_devel_label`.
-  It's possibile to develop and deploy your own descriptor. See :ref:`descriptor_devel_label`.

.. toctree::
   :maxdepth: 2
   :hidden:

   develop