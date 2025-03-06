FROM --platform=linux/amd64 python:3.10-bookworm AS build
EXPOSE 8000 1883
WORKDIR /app
COPY requirements.txt /app
RUN pip3 install -r requirements.txt --no-cache-dir

RUN apt-get update
RUN apt-get install -y iputils-ping
# uncomment if I need to exec into pod to manually troubleshoot mqtt
# RUN wget https://github.com/hivemq/mqtt-cli/releases/download/v4.37.0/mqtt-cli-4.37.0.deb
# RUN apt install ./mqtt-cli-4.37.0.deb

COPY . /app
ENTRYPOINT ["python3"]
CMD ["manage.py", "runserver", "0.0.0.0:8000"]