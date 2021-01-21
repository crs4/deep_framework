


from utils.abstract_descriptor import AbstractDescriptor


class ImgDescriptor(AbstractDescriptor):

      
    win_size = 10

    def detect_batch(self,detector_results,images):
      return ('img_desc_score', 0.5)
      

    def refine_classification(self,class_results):
      acc = 0
      for res in class_results:
        acc = acc + res[1]

      ref = float(acc/len(class_results))
      return ref
      
   