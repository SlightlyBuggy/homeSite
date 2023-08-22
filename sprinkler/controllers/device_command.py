import json
from django.views.decorators.csrf import csrf_exempt
import sprinkler.mqtt as mqtt


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

