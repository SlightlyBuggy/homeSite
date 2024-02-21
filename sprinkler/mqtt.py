import time

import paho.mqtt.client as mqtt
import json
from homeAutomation import settings
from sprinkler.models import DeviceStatusLog, IOTDevice
from util.automation_utils import get_voltage_from_ticks_and_cal, PSI_PER_PASCAL
from django.http import JsonResponse
from sprinkler.service.schedule_service import execute_scheduled_tasks, get_today_scheduled_tasks

# server to device topic
COMMAND_TOPIC = 'command'

# server to device commands
COMMAND_STATUS = 'status'
COMMAND_SPRINKLE_START = 'sprinkle_start'
COMMAND_SPRINKLE_ON = 'sprinkle_on'
COMMAND_SPRINKLE_OFF = 'sprinkle_off'
COMMAND_SLEEP = "sleep_now"
COMMAND_SWITCH_BROKER_DEBUG = "switch_broker_debug"
COMMAND_SWITCH_BROKER_PROD = "switch_broker_prod"
COMMAND_POWER_OFF = "power_off"

# device to server
DEVICE_MESSAGE_TOPIC = 'device_message'
DEVICE_SPRINKLE_START_TOPIC = 'sprinkle_start'
DEVICE_SPRINKLE_END_TOPIC = 'sprinkle_end'
DEVICE_STATUS_TOPIC = 'device_status'


def on_message(mqtt_client, userdata, msg):
    print(f'Received message on topic: {msg.topic} with payload: {msg.payload}')


def on_device_message(mqtt_client, userdata, msg):
    print(f'Received device message on topic: {msg.topic} with payload: {msg.payload}')


# TODO: the "execute scheduled tasks" may need to be pared down to checking the precip report
# TODO: also consider device status body, like 'just woke up' and 'just finished sprinkling' and 'pump commanded on', etc
def on_device_status(mqtt_client, userdata, msg):
    # TODO: this function is too long, and business logic shouldn't be in the mqtt module
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
            voltage = get_voltage_from_ticks_and_cal(input_ticks=voltage_ticks, cal_low_ticks=this_device.cal_low_ticks_voltage,
                                                     cal_low_voltage=this_device.cal_low_voltage,
                                                     cal_high_ticks=this_device.cal_high_ticks_voltage,
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

    # TODO: have process that ensures devices with a wake window eventually go to sleep, i.e. pings them for status

    pending_schedules, future_schedules_today = transmitting_device.today_active_schedules()

    # if we've got pending things to do, do them
    if pending_schedules:
        execute_scheduled_tasks(device=transmitting_device)
        return

    device_should_be_awake = transmitting_device.should_be_awake_now()

    # if the device should be awake now, don't tell it to do anything
    if device_should_be_awake:
        return

    device_should_be_awake_later_today = transmitting_device.should_be_awake_later_today()

    # if the device needs to be awake later today, or has things to do later today, put it to sleep
    if device_should_be_awake_later_today or future_schedules_today:
        payload = {
            'device_id': device_id,
            'command': COMMAND_SLEEP,
            'body': {
                'sleep_length_minutes': "60"  # TODO: this should vary so device wakes up right at start of wake window
            }
        }

        send_mqtt_message(COMMAND_TOPIC, str(payload))

        return

    # if we've made it here, the device doesn't have any tasks to accomplish now, doesn't need to be awake now,
    # doesn't need to be awake later, and has no tasks later.  It should be shut off for the day
    print(f"Telling device {device_id} to turn off")
    payload = {
        'device_id': device_id,
        'command': COMMAND_POWER_OFF,
    }
    print("Commanding device to turn off")
    send_mqtt_message(COMMAND_TOPIC, str(payload))

    return


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
