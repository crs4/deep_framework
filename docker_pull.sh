#!/bin/bash
registry="$1"
docker pull $registry/face_detection:deep_cpu
