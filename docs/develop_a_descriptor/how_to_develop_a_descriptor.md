# How to develop a descriptor

An algorithm of feature extraction can be developed with following operations:


1. Create a folder within the path [descriptor/feature_extractors](../../descriptor/feature_extractors).
2. Inside the folder, create, in a dedicated file, the class that implements the descriptor.
3. Inside the folder, create the descriptor configuration file.
4. Create the Dockerfiles.
5. Execute the test creation and execution procedure.

### Class definition
Each descriptor must extend the abstract class AbstractDescriptor, defined at the path [utils.abstract_descriptor](../../utils/abstract_descriptor.py)

image

For this reason the Descriptor class should implement:
* **win_size**: number of classification results that make up the time window on which an average will be averaged.
* **detect_batch**: is the method that given the list of incoming images (crop of detector detected objects, images) and the list of detector detected objects (detector_results), must return their classification.
  * detector_results is the dictionary produced by the detector and contains the following values:
    * frame_idx: id of the frame analysed by the detector
    * objects: list of objects detected by the detector in the frame_idx frame
    * fp_time: timestamp that identifies the instant in which the detector produces its results.  
    * vc_time: timestamp that identifies the instant of time in which the frame was captured. 
    * frame_shape: frame size.
* **refine_classification**: is the method that takes an input list of results (class_results) and returns the output results averaged over the maximum size of the time window on which they were captured represented by win_size.
  * class_results: is a list of results produced by detect_batch

Example:


image

### Configuration creation
The configuration file must be of type .ini and must contain the following fields:

* **NAME**: name associated with the descriptor
* **PATH**: path of the file containing the descriptor class, relative to the feature_extractors folder
* **CLASS**: class name of the descriptor
* **FRAMEWORK**: framework used by the descriptor (None if no framework is used)
* **RELATED_TO**: indicates which detector the descriptor is associated with. Enter the name of the detector category.
* **TYPE**: can take two values: 
  * object_oriented: the descriptor extracts a property of the object detected by the detector
  * image_oriented. the descriptor extracts an image property.
Example:
generic_configuration.ini

image

image


### Creation of dockerfiles
Inside your folder there must be at least one dockerfile for the creation of the component. In particular, a dockerfile must be prepared for each mode in which the descriptor is to be executed (cpu/gpu).
The following guidelines must be taken into account when creating dockerfiles:
* The Dockerfile for creating Docker images that will use only the cpu should be called Dockerfile.cpu
* The Dockerfile for creating Docker images that will use the gpu should be called Dockerfile.gpu
* Supporting Docker images should be named Dockerfile.setup if any.
Modify the Dockerfiles according to the comments in the example dockerfiles in the [generic_descriptor](../../descriptor/feature_extractors/generic_descriptor/) folder.

### Creation and execution of tests
Once the descriptor development and configuration procedure has been completed, the test procedure must be performed.
Execute the following command:
```
python3 test_creator.py
```

This command generates the scripts to test all the algorithms (detection and feature extraction) installed on the platform. For feature extraction algorithms, the tests are created in the following path:
[descriptor/descriptor_tests/test_scripts](../../descriptor/descriptor_tests/test_scripts).
To run a test, from the main folder, run the desired script. Example:
```
./descriptor/descriptor_tests/test_scripts/my_test.sh
```

