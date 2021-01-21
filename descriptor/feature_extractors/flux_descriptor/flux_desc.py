import pandas as pd
import numpy as np
from .flux import Flux
import json
import traceback as tb


from utils.abstract_descriptor import AbstractDescriptor

DECIMATION = 70
PERIOD = 30

class FluxDescriptor(AbstractDescriptor):

    def __init__(self):
      self.flux = Flux(1080, 720, decimation=DECIMATION, period=PERIOD)
      self.output = {}
      
    win_size = 10

    def detect_batch(self,detector_results,images):
      try:
        frame_width = detector_results['frame_shape'][1]
        frame_height = detector_results['frame_shape'][0]
        if frame_width != self.flux.frame_width or frame_height != self.flux.frame_height:
          self.flux = Flux(frame_width, frame_height, decimation=DECIMATION, period=PERIOD)

        x_c = []
        y_c = []
        ids = []
        if type(detector_results) != dict:
          raise Exception('detector_results is not dict')
        if 'objects' not in detector_results:
            raise Exception('objects is not in detector_results')
        if type(detector_results['objects']) != list:
          raise Exception('objects is not list')

        for det_obj in detector_results['objects']:
          if type(det_obj) != dict:
            raise Exception('det_obj is not dict')
          if 'rect' not in det_obj:
            raise Exception('rect is not in det_obj')
          if type(det_obj['rect']['x_topleft']) != int:
            raise Exception("det_obj['rect']['x_topleft'] is not int")
          x_c.append(det_obj['rect']['x_topleft'] + (det_obj['rect']['x_bottomright'] - det_obj['rect']['x_topleft']) / 2)
          y_c.append(det_obj['rect']['y_topleft'] + (det_obj['rect']['y_bottomright'] - det_obj['rect']['y_topleft']) / 2)
          ids.append(det_obj['pid'])

        detected_objects = pd.DataFrame({'x_c': x_c, 'y_c': y_c}, index=ids)
        timestamp = detector_results['vc_time']
        self.flux.update(detected_objects, timestamp)
        self.output = {
            # 'timestamp': round(timestamp, 3),
            # 'frame_shape': frame.shape,
            'grid_data': self.flux.grid_data,
            'period': self.flux.period,
            'flux_shape': self.flux.flux.shape,
            'velocity_shape': np.around(self.flux.avg_velocity, 1).shape,
            'occupation_shape': self.flux.occupation.shape,
            'flux': self.flux.flux.flatten().tolist(),
            'velocity': np.around(self.flux.avg_velocity, 1).flatten().tolist(),
            'occupation': self.flux.occupation.flatten().tolist(),
        }
        output_json = json.dumps(self.output, separators=(',', ':'))
        print('*** OUTPUT ***\n' + output_json)
      except Exception as e:
        tb.print_exc()
        raise e


      return ('flux_analysis', self.output)
      

    def refine_classification(self,class_results):
      
      return self.output
      
   