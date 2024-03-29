import paho.mqtt.client as mqtt
import json
from homeAutomation import settings
from sprinkler.models import DeviceStatusLog, IOTDevice
from util.automation_utils import get_voltage_from_ticks_and_cal, PSI_PER_PASCAL
from django.http import JsonResponse

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

    # TODO: include pressure ticks and conversion to pressure
    voltage_ticks = None
    voltage = None
    water_pressure_psi = None

    if 'voltage_ticks' in status:
        voltage_ticks = status['voltage_ticks']
        devices_with_device_id: list[IOTDevice] = IOTDevice.objects.filter(device_id=device_id)[:1]

        if devices_with_device_id:
            this_device: IOTDevice = devices_with_device_id[0]
            voltage = get_voltage_from_ticks_and_cal(input_ticks=voltage_ticks, cal_low_ticks=this_device.cal_low_ticks,
                                                     cal_low_voltage=this_device.cal_low_voltage,
                                                     cal_high_ticks=this_device.cal_high_ticks,
                                                     cal_high_voltage=this_device.cal_high_voltage)

    if 'pressure' in status:
        water_pressure_pascals = status['pressure']
        water_pressure_psi = water_pressure_pascals*PSI_PER_PASCAL

    transmitting_device = IOTDevice.objects.get(device_id=device_id)

    if not transmitting_device:
        print(f"Unable to handle device status message.  unknown device id {device_id}")
        return

    new_device_status = DeviceStatusLog(device=transmitting_device, supply_voltage=voltage,
                                        supply_voltage_ticks=voltage_ticks,
                                        water_pressure_psi=water_pressure_psi)
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


def send_mqtt_message(topic, body) -> JsonResponse:
    # TODO: validate message

    # cast body to string if needed
    if not type(body) == str:
        body = str(body)
    rc, mid = client.publish(topic, body)
    return JsonResponse({'code': rc})
