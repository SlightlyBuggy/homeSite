import json
import sprinkler.mqtt as mqtt


# TODO: make these get/post/put only as needed
# TODO: incorporate csrf protection
def publish_message(request):
    # TODO: validate request body
    request_data = json.loads(request.body)

    mqtt_response = mqtt.send_mqtt_message(request_data['topic'], request_data['body'])
    return mqtt_response
