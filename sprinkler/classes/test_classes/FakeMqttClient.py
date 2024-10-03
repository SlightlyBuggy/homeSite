from sprinkler.classes.AbstractMqttClient import AbstractMqttClient
from sprinkler.classes.test_classes.ParsedDeviceToServerStatusMessage import ParsedDeviceToServerStatusMessage
from sprinkler.classes.test_classes.MockDeviceToServerStatusMessage import RawDeviceToServerStatusMessage
from sprinkler.service.device_service import handle_device_status
from sprinkler.constants import COMMAND_TOPIC
from sprinkler.models import ServerToDeviceCommand
import ast
from django.http import JsonResponse


class FakeMqttClient(AbstractMqttClient):

    client = None

    def __init__(self):
        self.init_mqtt()

    def on_device_status(self, mqtt_client, userdata, msg):

        parsed_message = ParsedDeviceToServerStatusMessage(msg)

        handle_device_status(parsed_message.device_id, parsed_message.status)

    def on_device_status(self, mqtt_client, userdata, msg):
        parsed_message = ParsedDeviceToServerStatusMessage(msg)

        handle_device_status(parsed_message.device_id, parsed_message.status)

    def on_connect(self, mqtt_client, userdata, flags, rc):
        pass

    def on_disconnect(self, mqtt_client, userdata, rc):
        pass

    def init_mqtt(self):
        pass

    # TODO: this shouldn't happen when we have command/ack
    @staticmethod
    def handle_command_without_response(command):
        print(f"Command {command} sent, no response expected")

    def send_mqtt_message(self, topic, body) -> JsonResponse:

        # cast body to string if needed
        if not type(body) == str:
            body = str(body)

        if topic != COMMAND_TOPIC:
            raise Exception(f"Unknown topic {topic}")

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

        # TODO: this should hand off to a device mocker
        # TODO: uncle bob says these should be hidden behind an abstract factory.  maybe we can do that later.
        # given the command we are going to send, craft the response we expect to see from the device and send
        # that to the appropriate handler
        match command:
            case ServerToDeviceCommand.STATUS.value:
                raw_device_to_server_message = RawDeviceToServerStatusMessage(topic=topic, device_id=device_id)
                self.on_device_status(None, None, raw_device_to_server_message)
            case ServerToDeviceCommand.SLEEP.value:
                self.handle_command_without_response(command)
            case ServerToDeviceCommand.POWER_OFF.value:
                self.handle_command_without_response(command)
            case ServerToDeviceCommand.SPRINKLE_ON.value:
                self.handle_command_without_response(command)
            case ServerToDeviceCommand.SPRINKLE_OFF.value:
                self.handle_command_without_response(command)
            case ServerToDeviceCommand.SPRINKLE_START.value:
                self.handle_command_without_response(command)
            case ServerToDeviceCommand.SWITCH_BROKER_DEBUG.value:
                self.handle_command_without_response(command)
            case ServerToDeviceCommand.SWITCH_BROKER_PROD.value:
                self.handle_command_without_response(command)

            case _:
                raise Exception(f"Unknown command {command}")

        return JsonResponse({'code': 0})