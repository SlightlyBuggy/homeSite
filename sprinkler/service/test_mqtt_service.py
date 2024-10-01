from django.test import TestCase
from sprinkler.factories.iotdevice_factory import create_device
from sprinkler.models import IOTDevice
from sprinkler.service import mqtt_service
from sprinkler.constants import COMMAND_TOPIC
from sprinkler.models import ServerToDeviceCommand


class TestMqttService(TestCase):

    test_device: IOTDevice

    def setUp(self):
        self.test_device = create_device()

    def test_send_message_with_dict_body(self):
        try:
            mqtt_service.client.send_mqtt_message(COMMAND_TOPIC, {'device_id': self.test_device.device_id,
                                                                  'command': ServerToDeviceCommand.STATUS.value})
        except Exception as e:
            self.fail("mqtt_service.send_mqtt_message unexpectedly raised exception when sending dict body")

    def test_send_message_with_text_body(self):
        try:
            mqtt_service.client.send_mqtt_message(COMMAND_TOPIC, str({'device_id': self.test_device.device_id,
                                                                      'command': ServerToDeviceCommand.STATUS.value}))
        except Exception as e:
            self.fail("mqtt_service.send_mqtt_message unexpectedly raised exception when sending str body")
