

#!/bin/bash

registry="$1"



docker pull $registry/face_detector:deep
docker pull $registry/collector:deep
docker pull $registry/broker:deep
docker pull $registry/sub_collector:deep
docker pull $registry/monitor:deep
docker pull $registry/yaw:deep_cpu
docker pull $registry/face_recognition:deep_cpu
docker pull $registry/age:deep_cpu
docker pull $registry/emotion:deep_cpu
docker pull $registry/gender:deep_cpu
docker pull $registry/glasses:deep_cpu
docker pull $registry/pitch:deep_cpu
docker pull $registry/yaw:deep_gpu
docker pull $registry/face_recognition:deep_gpu
docker pull $registry/age:deep_gpu
docker pull $registry/emotion:deep_gpu
docker pull $registry/gender:deep_gpu
docker pull $registry/glasses:deep_gpu
docker pull $registry/pitch:deep_gpu
docker pull $registry/server:deep
docker pull $registry/stream_capture:deep
docker pull $registry/stream_manager:deep
