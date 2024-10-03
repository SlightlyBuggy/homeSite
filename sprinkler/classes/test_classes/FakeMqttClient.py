from sprinkler.classes.AbstractMqttClient import AbstractMqttClient
from sprinkler.classes.test_classes.ParsedDeviceToServerStatusMessage import ParsedDeviceToServerStatusMessage
from sprinkler.classes.test_classes.MockDeviceToServerStatusMessage import MockDeviceToServerStatusMessage
from sprinkler.service.device_service import handle_device_status
from sprinkler.constants import COMMAND_TOPIC
from sprinkler.models import ServerToDeviceCommand
import ast
from django.http import JsonResponse
import sprinkler.classes.test_classes.DeviceMocker as Mocker


class FakeMqttClient(AbstractMqttClient):

    client = None
    device_mocker = None

    def __init__(self):
        self.init_mqtt()
        self.device_mocker = Mocker.device_mocker

    def on_device_status(self, mqtt_client, userdata, msg):

        parsed_message = ParsedDeviceToServerStatusMessage(msg)

        handle_device_status(parsed_message.device_id, parsed_message.status)

    def on_connect(self, mqtt_client, userdata, flags, rc):
        pass

    def on_disconnect(self, mqtt_client, userdata, rc):
        pass

    def init_mqtt(self):
        pass

    @staticmethod
    def validate_body_and_get_command_and_device_id(body):
        # cast body to string if needed
        if not type(body) == str:
            body = str(body)

        # for the test, we want to simulate the device immediately responding
        # first unpack the command so we know the appropriate way the device should respond
        json_body = ast.literal_eval(body)

        try:
            command = json_body['command']
        except KeyError:
            raise KeyError(f"Missing 'command' from body {body}")

        try:
            device_id = json_body['device_id']
        except KeyError:
            raise KeyError(f"Missing 'device_id' from body {body}")

        return command, device_id

    def send_mqtt_message(self, topic, body) -> JsonResponse:

        if topic != COMMAND_TOPIC:
            raise Exception(f"Unknown topic {topic}")

        command, device_id = self.validate_body_and_get_command_and_device_id(body)

        self.device_mocker.mock_device_response_to_command(device_id=device_id, command=command)

        return JsonResponse({'code': 0})
