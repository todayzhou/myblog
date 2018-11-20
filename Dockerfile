FROM python:3.6-alpine

RUN adduser -D myblog

WORKDIR /home/myblog

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn

COPY app app
COPY migrations migrations
COPY run.py config.py boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP run.py

RUN chown -R myblog:myblog ./
USER myblog

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
