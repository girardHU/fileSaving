FROM python:3.7-buster

# COPY ./api/app.py /api

ENV FLASK_RUN_HOST=0.0.0.0
# ENV FLASK_RUN_PORT=5000
ENV FLASK_APP=app.py
ENV FLASK_ENV=development

RUN apt-get update
RUN pip install flask sqlalchemy flask-sqlalchemy pymysql

# EXPOSE 5000

ENTRYPOINT ["flask", "run"]