import paho.mqtt.client as mqtt
from . import settings


def on_message(mqtt_client, userdata, msg):
    print(f'Received message on topic: {msg.topic} with payload: {msg.payload}')


def on_connect(mqtt_client, userdata, flags, rc):
    if rc == 0:
        print('Connected to mqtt server')
        # mqtt_client.subscribe('django/mqtt')
        mqtt_client.subscribe('device_messages')
    else:
        print('Bad connection. Code:', rc)


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set(settings.MQTT_USER, settings.MQTT_PASSWORD)
client.connect(
    host=settings.MQTT_SERVER,
    port=settings.MQTT_PORT,
    keepalive=settings.MQTT_KEEPALIVE
)