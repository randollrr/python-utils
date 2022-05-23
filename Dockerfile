FROM  python:3.10-slim-bullseye

COPY ./requirements.txt /opt/
RUN pip3 install -r /opt/requirements.txt
