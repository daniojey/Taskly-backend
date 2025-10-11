FROM python:3.14.0rc3-bookworm


WORKDIR /app


COPY requirements.txt requirements.txt


RUN pip install -r requirements.txt


COPY /Django /app
COPY .env /app


CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]