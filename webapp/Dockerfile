FROM python:3.13.0-slim-bookworm

WORKDIR /app

COPY requirements.txt /app

COPY backend/db_models /app/backend/db_models

COPY backend/databaseinit.py /app/backend

RUN pip install -r requirements.txt

RUN cd /var/lib && mkdir db_data && chmod -R 777 db_data

RUN chmod -R 777 /var/lib/db_data

RUN cd backend && python3 databaseinit.py