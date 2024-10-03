import sprinkler.service.mqtt_service as mqtt
from sprinkler.classes.test_classes.MockDeviceToServerStatusMessage import MockDeviceToServerStatusMessage
from sprinkler.models import ServerToDeviceCommand


class DeviceMocker:

    @staticmethod
    def _handle_command_without_response(command):
        print(f"Response for command {command} not implemented")

    @staticmethod
    def _mock_response_to_status_command(device_id):
        mock_device_to_server_message = MockDeviceToServerStatusMessage(device_id=device_id)
        mqtt.client.on_device_status(None, None, mock_device_to_server_message)

    def mock_device_response_to_command(self, device_id, command):
        match command:
            case ServerToDeviceCommand.STATUS.value:
                self._mock_response_to_status_command(device_id=device_id)
            case ServerToDeviceCommand.SLEEP.value:
                self._handle_command_without_response(command)
            case ServerToDeviceCommand.POWER_OFF.value:
                self._handle_command_without_response(command)
            case ServerToDeviceCommand.SPRINKLE_ON.value:
                self._handle_command_without_response(command)
            case ServerToDeviceCommand.SPRINKLE_OFF.value:
                self._handle_command_without_response(command)
            case ServerToDeviceCommand.SPRINKLE_START.value:
                self._handle_command_without_response(command)
            case ServerToDeviceCommand.SWITCH_BROKER_DEBUG.value:
                self._handle_command_without_response(command)
            case ServerToDeviceCommand.SWITCH_BROKER_PROD.value:
                self._handle_command_without_response(command)
            case _:
                raise Exception(f"Unknown command {command}")


device_mocker = DeviceMocker()
