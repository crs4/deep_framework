
Architecture
------------

.. figure:: schemes.png
   :alt: architecture scheme

The architecture of Deep Framework is composed by the following generic
components: 

* **Stream Manager**: establishes the connection with the video source in order to grab the individual frames and send them, together with a timestamp, to the processing components. It also gets the results from the collectors and stream video and data to any WebRTC peer.
* **Detector**: this component is responsible for extracting the coordinates of an object in an image and for tracking it along all received images. The object could be an entity that is depicted in a particular region of the image or in the entire image.
* **Broker**: receives data from the Detector and distributes them across all the instances of the Descriptor. 
* **Descriptor**: carries out the analysis of the ROIs and/or coordinates, retrieved by the Detector, in order ton extract information about objects and/or their trajectories.
* **SubCollector**: it aggregates the results obtained by the workers instantiated for each Descriptor.
* **Collector**: for every result coming from Detector (objects coordinates, identifiers), it produces an output message aggregating the latest available results obtained from Sub Collectors.
* **Monitor**: is connected with all pipeline components and receives and aggregates from them their operating metrics. 
* **Server**: provides results and stats via a SSE API. It also act as a WebRTC signaling server and provides the demo web app.