#!/bin/bash
registry="$1"
docker pull $registry/stream_capture:deep
docker pull $registry/collector:deep
docker pull $registry/server:deep
docker pull $registry/face_detection:deep_cpu
docker pull $registry/person_detection:deep
docker pull $registry/drone_object_detector:deep_gpu
docker pull $registry/stream_manager:deep
docker pull $registry/monitor:deep
docker pull $registry/broker:deep
docker pull $registry/sub_collector:deep
docker pull $registry/gender_detection:deep_cpu
docker pull $registry/gender_detection:deep_gpu
docker pull $registry/age_detection:deep_cpu
docker pull $registry/age_detection:deep_gpu
docker pull $registry/glasses_detection:deep_cpu
docker pull $registry/glasses_detection:deep_gpu
docker pull $registry/pitch_detection:deep_cpu
docker pull $registry/pitch_detection:deep_gpu
docker pull $registry/face_recognition:deep_cpu
docker pull $registry/face_recognition:deep_gpu
docker pull $registry/yaw_detection:deep_cpu
docker pull $registry/yaw_detection:deep_gpu
docker pull $registry/emotion_detection:deep_cpu
docker pull $registry/emotion_detection:deep_gpu
