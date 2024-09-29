FROM python:3.12.3-slim

WORKDIR /app

COPY . /app

RUN python3 -m pip install -r requirements.txt
RUN ["pip", "install", "zmq", "pyzmq", "sortedcontainers"]