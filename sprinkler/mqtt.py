import paho.mqtt.client as mqtt
import json
from homeAutomation import settings
from sprinkler.models import DeviceStatusLog, IOTDevice

# server to device topic
COMMAND_TOPIC = 'command'

# server to device commands
COMMAND_STATUS = 'status'
COMMAND_SPRINKLE_START = 'sprinkle_start'
COMMAND_SPRINKLE_ON = 'sprinkle_on'
COMMAND_SPRINKLE_OFF = 'sprinkle_off'

# device to server
DEVICE_MESSAGE_TOPIC = 'device_message'
DEVICE_SPRINKLE_START_TOPIC = 'sprinkle_start'
DEVICE_SPRINKLE_END_TOPIC = 'sprinkle_end'
DEVICE_STATUS_TOPIC = 'device_status'


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

    pressure = None
    voltage = None

    if 'pressure' in status:
        pressure = status['pressure']

    if 'voltage' in status:
        voltage = status['voltage']

    transmitting_device = IOTDevice.objects.get(device_id=device_id)

    if not transmitting_device:
        print(f"Unable to handle device status message.  unknown device id {device_id}")
        return

    new_device_status = DeviceStatusLog(device=transmitting_device, supply_voltage=voltage, water_level_inches=pressure)
    new_device_status.save()


def on_sprinkle_start(mqtt_client, userdata, msg):
    print(f'Received sprinkle start message on topic: {msg.topic} with payload: {msg.payload}')


def on_sprinkle_end(mqtt_client, userdata, msg):
    print(f'Received sprinkle end message on topic: {msg.topic} with payload: {msg.payload}')


def on_connect(mqtt_client, userdata, flags, rc):
    if rc == 0:
        print('Connected to mqtt server')
        mqtt_client.subscribe(DEVICE_MESSAGE_TOPIC)
        mqtt_client.subscribe(DEVICE_STATUS_TOPIC)
        mqtt_client.subscribe(DEVICE_SPRINKLE_START_TOPIC)
        mqtt_client.subscribe(DEVICE_SPRINKLE_END_TOPIC)
    else:
        print('Bad connection. Code:', rc)


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
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