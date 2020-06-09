

FROM ufoym/deepo:cpu



RUN pip3 install \
    imutils==0.5.2 \
    pyzmq==18.0.1 \
    opencv-python==4.1.0.25 \
    opencv-contrib-python==4.2.0.34



COPY . /home/deepframework/detector/face_detection

COPY --from=utils:deep /home/deepframework/utils /home/deepframework/detector/face_detection/utils


WORKDIR /home/deepframework/detector/face_detection

CMD python face_provider.py
