FROM --platform=$BUILDPLATFORM python:3.10-bookworm AS builder
EXPOSE 8000 1883
WORKDIR /app
COPY requirements.txt /app
RUN pip3 install -r requirements.txt --no-cache-dir

RUN apt-get update
RUN apt-get install -y iputils-ping

COPY . /app
ENTRYPOINT ["python3"]
CMD ["manage.py", "runserver", "0.0.0.0:8000"]