#!/bin/bash
registry="$1"
docker pull $registry/monitor:deep
docker pull $registry/collector:deep
docker pull $registry/server:deep
docker pull $registry/stream_manager:deep
docker pull $registry/gender_detection:deep_gpu
docker pull $registry/glasses_detection:deep_gpu
docker pull $registry/broker:deep
docker pull $registry/sub_collector:deep
docker pull $registry/stream_capture:deep
