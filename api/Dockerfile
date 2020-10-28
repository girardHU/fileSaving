FROM python:3.7-buster

ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_APP=/code/source/app.py
ENV FLASK_ENV=development

RUN pip install flask sqlalchemy flask-sqlalchemy pymysql cryptography

ENTRYPOINT ["flask", "run"]
