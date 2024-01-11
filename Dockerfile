FROM  python:3.10-slim-bullseye

ENV APP_NAME=python-utils

COPY src/app/ /opt/${APP_NAME}/
RUN pip3 install -r /opt/${APP_NAME}/requirements.txt
