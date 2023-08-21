import json
import util.automation_utils as util


# TODO: make these get/post/put only as needed
# TODO: incorporate csrf protection
def publish_message(request):
    # TODO: validate request body
    request_data = json.loads(request.body)

    mqtt_response = util.send_mqtt_message(request_data['topic'], request_data['body'])
    return mqtt_response
