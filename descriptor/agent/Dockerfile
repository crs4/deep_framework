
FROM python:3.7-slim

RUN pip3 install \
    pyzmq==18.0.1

RUN mkdir -p /home/deepframework/agent

COPY . /home/deepframework/agent
COPY --from=utils:deep /home/deepframework/utils/. /home/deepframework/agent/utils


WORKDIR /home/deepframework/agent

