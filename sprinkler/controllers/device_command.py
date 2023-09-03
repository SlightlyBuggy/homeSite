import json
from django.views.decorators.csrf import csrf_exempt
import sprinkler.mqtt as mqtt

# TODO: validation for all requests
# TODO: fix so we don't do csrf_exempt


@csrf_exempt
def status(request):
    request_data = json.loads(request.body)

    device_id = request_data['device_id']

    test_payload = {'device_id': device_id, 'command': mqtt.COMMAND_STATUS, 'body': {}}

    mqtt_response = mqtt.send_mqtt_message(mqtt.COMMAND_TOPIC, str(test_payload))
    return mqtt_response


@csrf_exempt
def sprinkle_start(request):
    request_data = json.loads(request.body)

    device_id = request_data['device_id']

    test_payload = {
        'device_id': device_id,
        'command': mqtt.COMMAND_SPRINKLE_START,
        'body': {}
    }

    # add request params
    if 'watering_length_minutes' in request_data:
        test_payload['body']['watering_length_minutes'] = request_data['watering_length_minutes']

    if 'watering_length_seconds' in request_data:
        test_payload['body']['watering_length_seconds'] = request_data['watering_length_seconds']

    mqtt_response = mqtt.send_mqtt_message(mqtt.COMMAND_TOPIC, str(test_payload))
    return mqtt_response


@csrf_exempt
def sprinkle_on(request):
    request_data = json.loads(request.body)

    device_id = request_data['device_id']

    payload = {
        'device_id': device_id,
        'command': mqtt.COMMAND_SPRINKLE_ON
    }

    mqtt_response = mqtt.send_mqtt_message(mqtt.COMMAND_TOPIC, str(payload))
    return mqtt_response


@csrf_exempt
def sprinkle_off(request):
    request_data = json.loads(request.body)

    device_id = request_data['device_id']

    payload = {
        'device_id': device_id,
        'command': mqtt.COMMAND_SPRINKLE_OFF
    }

    mqtt_response = mqtt.send_mqtt_message(mqtt.COMMAND_TOPIC, str(payload))
    return mqtt_response


@csrf_exempt
def sleep_now(request):
    request_data = json.loads(request.body)

    device_id = request_data['device_id']

    sleep_length_minutes = 1
    if 'sleep_length_minutes' in request_data:
        sleep_length_minutes = request_data['sleep_length_minutes']

    payload = {
        'device_id': device_id,
        'command': mqtt.COMMAND_SLEEP,
        'body': {
            'sleep_length_minutes': str(sleep_length_minutes)
        }
    }

    mqtt_response = mqtt.send_mqtt_message(mqtt.COMMAND_TOPIC, str(payload))
    return mqtt_response


@csrf_exempt
def switch_broker_debug(request):
    request_data = json.loads(request.body)

    device_id = request_data['device_id']

    payload = {
        'device_id': device_id,
        'command': mqtt.COMMAND_SWITCH_BROKER_DEBUG
    }

    mqtt_response = mqtt.send_mqtt_message(mqtt.COMMAND_TOPIC, str(payload))
    return mqtt_response


@csrf_exempt
def switch_broker_prod(request):
    request_data = json.loads(request.body)

    device_id = request_data['device_id']

    payload = {
        'device_id': device_id,
        'command': mqtt.COMMAND_SWITCH_BROKER_PROD
    }

    mqtt_response = mqtt.send_mqtt_message(mqtt.COMMAND_TOPIC, str(payload))
    return mqtt_response

