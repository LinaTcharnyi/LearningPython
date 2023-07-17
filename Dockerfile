FROM python:3.6
MAINTAINER "Franklin Koch <franklin.koch@seequent.com>"

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY requirements.txt /usr/src/app/
RUN pip install -r requirements.txt
COPY app.py /usr/src/app/

CMD python -u app.py
