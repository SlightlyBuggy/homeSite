import paho.mqtt.client as mqtt
from homeAutomation import settings
from django.http import JsonResponse
import sprinkler.constants as spinkler_constants
from sprinkler.service.device_service import handle_device_status
from sprinkler.classes.DeviceToServerStatusMessage import DeviceToServerStatusMessage

client = None


def on_device_status(mqtt_client, userdata, msg):

    parsed_message = DeviceToServerStatusMessage(msg)

    handle_device_status(parsed_message.device_id, parsed_message.status, send_mqtt_message)


def on_connect(mqtt_client, userdata, flags, rc):
    if rc == 0:
        print('Connected to mqtt server')
        mqtt_client.subscribe(spinkler_constants.DEVICE_STATUS_TOPIC)
    else:
        print('Bad connection. Code:', rc)


def on_disconnect(mqtt_client, userdata, rc):
    if rc != 0:
        print(f"Unexpected disconnect from mqtt broker with code {rc}")


# not sure how i feel about this.  on one hand, its nice to have to take an on-purpose action to connect to the broker
# on the other, we have to know to do this
def init_mqtt():
    global client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.message_callback_add(spinkler_constants.DEVICE_STATUS_TOPIC, on_device_status)
    client.username_pw_set(settings.MQTT_USER, settings.MQTT_PASSWORD)
    client.connect(
        host=settings.MQTT_SERVER,
        port=settings.MQTT_PORT,
        keepalive=settings.MQTT_KEEPALIVE
    )
    client.loop_start()


def send_mqtt_message(topic, body) -> JsonResponse:
    # TODO: validate message

    if not client:
        raise Exception("mqtt client has not been initialized")

    # cast body to string if needed
    if not type(body) == str:
        body = str(body)
    rc, mid = client.publish(topic, body)
    return JsonResponse({'code': rc})
