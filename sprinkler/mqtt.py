import paho.mqtt.client as mqtt
import json
from homeAutomation import settings
from django.http import JsonResponse
import sprinkler.constants as spinkler_constants
from sprinkler.service.device_service import handle_device_status


def on_message(mqtt_client, userdata, msg):
    print(f'Received message on topic: {msg.topic} with payload: {msg.payload}')


def on_device_message(mqtt_client, userdata, msg):
    print(f'Received device message on topic: {msg.topic} with payload: {msg.payload}')


def on_device_status(mqtt_client, userdata, msg):
    print(f'Received device status message on topic: {msg.topic} with payload: {msg.payload}')
    message_contents = json.loads(msg.payload)
    if 'device_id' not in message_contents:
        print("Unable to handle status message.  'device_id' not present")
        return

    if 'status' not in message_contents:
        print("Unable to handle status message.  'status' not present.")

    device_id = message_contents['device_id']
    status = message_contents['status']

    handle_device_status(device_id, status, send_mqtt_message)


def on_sprinkle_start(mqtt_client, userdata, msg):
    print(f'Received sprinkle start message on topic: {msg.topic} with payload: {msg.payload}')


def on_sprinkle_end(mqtt_client, userdata, msg):
    print(f'Received sprinkle end message on topic: {msg.topic} with payload: {msg.payload}')


def on_connect(mqtt_client, userdata, flags, rc):
    if rc == 0:
        print('Connected to mqtt server')
        mqtt_client.subscribe(spinkler_constants.DEVICE_MESSAGE_TOPIC)
        mqtt_client.subscribe(spinkler_constants.DEVICE_STATUS_TOPIC)
        mqtt_client.subscribe(spinkler_constants.DEVICE_SPRINKLE_START_TOPIC)
        mqtt_client.subscribe(spinkler_constants.DEVICE_SPRINKLE_END_TOPIC)
    else:
        print('Bad connection. Code:', rc)


def on_disconnect(mqtt_client, userdata, rc):
    if rc != 0:
        print(f"Unexpected disconnect from mqtt broker with code {rc}")


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect
client.message_callback_add('device_status', on_device_status)
client.message_callback_add('device_message', on_device_message)
client.message_callback_add('sprinkle_start', on_sprinkle_start)
client.message_callback_add('sprinkle_end', on_sprinkle_end)
client.username_pw_set(settings.MQTT_USER, settings.MQTT_PASSWORD)
client.connect(
    host=settings.MQTT_SERVER,
    port=settings.MQTT_PORT,
    keepalive=settings.MQTT_KEEPALIVE
)


def send_mqtt_message(topic, body) -> JsonResponse:
    # TODO: validate message

    # cast body to string if needed
    if not type(body) == str:
        body = str(body)
    rc, mid = client.publish(topic, body)
    return JsonResponse({'code': rc})
