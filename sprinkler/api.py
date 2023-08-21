import json
from django.views.decorators.csrf import csrf_exempt
import util.automation_utils as util
import sprinkler.mqtt as mqtt


@csrf_exempt
def test_device_command_status(request):
    request_data = json.loads(request.body)

    device_id = request_data['device_id']

    test_payload = {'device_id': device_id, 'command': mqtt.COMMAND_STATUS, 'body': {}}

    mqtt_response = util.send_mqtt_message(mqtt.COMMAND_TOPIC, str(test_payload))
    return mqtt_response