

Usage
-------

Using the Deep-Framework Demo Web Application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One of the services that are included in the Deep-Framework once it's up and running is a demo application that allows to visualize and manage the video stream, the resulting data stream, and the performance of the Deep-Framework services and algorithms from any web browser. This web app can be accessed at `https://<IP_ADDRESS_OF_THE_MAIN_NODE>:8000` and provides three main views:

    * **CONTROLS**: Here are the controls for establishing the WebRTC peer connection with the Server, selecting the Stream Manager to peer with, and selecting and starting the video stream. The source of the video stream can be either a IP camera (the camera URL has to be previously defined during the guided CLI starting procedure) or the webcam of the client device.
    * **DASHBOARD**: This is the panel for monitoring the state and performance of the Deep-Framework services and algorithms.
    * **VIEWER**: Provides the a user friendly interface for visualizing the video stream and the resulting data. Some results like the face detection boxes, and the yaw and pitch angles are graphically represented as an overlay of the video stream. 
    * **API DOCS**: Provides the API documentation for the specific configuration set by the user.

Using a custom web application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can interact directly with the Server and the Stream Manager from your browser-based application by using the `hyperpeer-js module <https://github.com/crs4/hyperpeer-js>`__ (Deep-Framework video streaming is based on `Hyperpeer <http://www.crs4.it/results/technology-catalogue/hyperpeer/>`__ which in turn is based on `WebRTC <https://en.wikipedia.org/wiki/WebRTC>`__). You can install this javascript library (currently available only through its GitHub repo) and using it in your code using browserify or any other frontend package manager. In :ref:`custom_web_app_label`, you can find a simplified example that illustrates how to use `hyperpeer-js <https://github.com/crs4/hyperpeer-js>`__ for sending the local webcam video stream and get the results as ``data`` events. See `hyperpeer-js <https://github.com/crs4/hyperpeer-js>`__ documentation for more details.


.. toctree::
   :maxdepth: 2
   :hidden:

   custom_app_example

Using the SSE API
~~~~~~~~~~~~~~~~~

The web app (either the demo or a custom one) is the main interface for controlling and monitoring the analysis of a video stream with the Deep-Framework. However, it connects to the Stream Manager with a peer-to-peer connection so only one client application can be used at a time. If you need to send the video analysis results to another or many other applications you can use the SSE API which provides multiple endpoints (consider that analysis has been started through the web app first in order to receive any data):

  * ``/api/stream_<DETECTOR_CATEGORY>``: there is an endpoint for every detector chosen.
  * ``/api/stats``: it shows functioning statistics about the components running in the pipelines. 
  * ``/api/algs``: it shows running alghorithms.