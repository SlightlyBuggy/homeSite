import json
from django.views.decorators.csrf import csrf_exempt
import sprinkler.service.mqtt_service as mqtt
from sprinkler.models import ServerToDeviceCommand, IOTDevice
import sprinkler.constants as constants
from sprinkler.service.command_service import send_command

# TODO: validation for all requests
# TODO: fix so we don't do csrf_exempt


@csrf_exempt
def status(request):
    device = get_device_from_request(request.body)

    mqtt_response = send_command(device=device, command=ServerToDeviceCommand.STATUS, command_body={})

    return mqtt_response


@csrf_exempt
def sprinkle_start(request):
    request_data = json.loads(request.body)

    device = get_device_from_request(request.body)

    command_body = {}

    # add request params
    if 'watering_length_minutes' in request_data:
        command_body['watering_length_minutes'] = request_data['watering_length_minutes']

    if 'watering_length_seconds' in request_data:
        command_body['watering_length_seconds'] = request_data['watering_length_seconds']

    if 'watering_wait_minutes' in request_data:
        command_body['watering_wait_minutes'] = request_data['watering_wait_minutes']

    if 'watering_repetitions' in request_data:
        command_body['watering_repetitions'] = request_data['watering_repetitions']

    mqtt_response = send_command(device=device, command=ServerToDeviceCommand.SPRINKLE_START.value,
                                 command_body=command_body)

    return mqtt_response

@csrf_exempt
def sprinkle_on(request):
    device = get_device_from_request(request.body)

    mqtt_response = send_command(device=device, command=ServerToDeviceCommand.SPRINKLE_ON.value)

    return mqtt_response


@csrf_exempt
def sprinkle_off(request):
    device = get_device_from_request(request.body)

    mqtt_response = send_command(device=device, command=ServerToDeviceCommand.SPRINKLE_OFF.value)
    return mqtt_response


@csrf_exempt
def sleep_now(request):
    device = get_device_from_request(request.body)

    request_data = json.loads(request.body)

    sleep_length_minutes = 1
    if 'sleep_length_minutes' in request_data:
        sleep_length_minutes = request_data['sleep_length_minutes']

    command_body = {'sleep_length_minutes': str(sleep_length_minutes)}

    mqtt_response = send_command(device=device, command=ServerToDeviceCommand.SLEEP.value,
                                 command_body=command_body)
    return mqtt_response

@csrf_exempt
def switch_broker_debug(request):
    device = get_device_from_request(request.body)

    mqtt_response = send_command(device=device, command=ServerToDeviceCommand.SWITCH_BROKER_DEBUG.value)
    return mqtt_response


@csrf_exempt
def switch_broker_prod(request):
    device = get_device_from_request(request.body)

    mqtt_response = send_command(device=device, command=ServerToDeviceCommand.SWITCH_BROKER_PROD.value)
    return mqtt_response

@csrf_exempt
def power_off(request):

    device = get_device_from_request(request.body)

    mqtt_response = send_command(device=device, command=ServerToDeviceCommand.POWER_OFF.value)

    return mqtt_response

def get_device_from_request(request_body: str):
    request_data = json.loads(request_body)
    device_id = request_data['device_id']
    device = IOTDevice.objects.get(device_id=device_id)
    return device


