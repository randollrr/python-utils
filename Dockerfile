FROM python:3.7-slim-buster

COPY ./requirements.txt /opt/
RUN pip3 install -r /opt/requirements.txt
