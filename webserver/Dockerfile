FROM python:3.13.0-slim-bookworm

WORKDIR /app

COPY requirements.txt /app

COPY src/db_models /app/src/db_models

COPY src/databaseinit.py /app/src

RUN pip install -r requirements.txt

RUN cd /var/lib && mkdir db_data && chmod -R 777 db_data

RUN chmod -R 777 /var/lib/db_data

RUN cd src && python3 databaseinit.py