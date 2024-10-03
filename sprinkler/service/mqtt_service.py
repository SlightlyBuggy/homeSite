from sprinkler.classes.RealMqttClient import RealMqttClient
from sprinkler.classes.test_classes.FakeMqttClient import FakeMqttClient


client = None


def initialize_and_start_real_mqtt():
    global client
    client = RealMqttClient()


def initialize_and_start_fake_mqtt():
    global client
    client = FakeMqttClient()
