#!/bin/bash
registry="$1"
docker pull $registry/gender_detection:deep_cpu
