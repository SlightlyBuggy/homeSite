from django.test import TestCase
from sprinkler.factories.iotdevice_factory import create_device
from sprinkler.models import IOTDevice
from sprinkler.service import mqtt_service
from sprinkler.constants import DEVICE_STATUS_TOPIC, COMMAND_TOPIC


class TestMqttService(TestCase):

    test_device: IOTDevice
    test_topic = "test"

    def setUp(self):
        self.test_device = create_device()

    def test_send_message_with_dict_body(self):
        try:
            mqtt_service.send_mqtt_message(self.test_topic, {"key": "val"})
        except Exception as e:
            self.fail("mqtt_service.send_mqtt_message unexpectedly raised exception when sending dict body")

    def test_send_message_with_text_body(self):
        try:
            mqtt_service.send_mqtt_message(self.test_topic, str({"key": "val"}))
        except Exception as e:
            self.fail("mqtt_service.send_mqtt_message unexpectedly raised exception when sending str body")
