from abc import ABC, abstractmethod
from django.http import JsonResponse


class AbstractMqttClient(ABC):

    @abstractmethod
    def on_device_status(self, mqtt_client, userdata, msg):
        pass

    @abstractmethod
    def on_connect(self, mqtt_client, userdata, flags, rc):
        pass

    @abstractmethod
    def on_disconnect(self, mqtt_client, userdata, rc):
        pass

    @abstractmethod
    def init_mqtt(self):
        pass

    @abstractmethod
    def send_mqtt_message(self, topic, body) -> JsonResponse:
        pass