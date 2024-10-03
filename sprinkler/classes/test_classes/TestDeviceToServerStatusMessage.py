from django.test import TestCase
from sprinkler.classes.test_classes.ParsedDeviceToServerStatusMessage import ParsedDeviceToServerStatusMessage
import json


class FakeRawMessage:
    def __init__(self, topic, payload):

        self.topic = topic
        self.payload = payload


class TestDeviceToServerStatusMessage(TestCase):

    test_topic = 'test_topic'

    def test_good_message(self):

        status = {'key': 'val'}
        payload = {'device_id': 0,
                   'status': status
                   }

        fake_message = FakeRawMessage(self.test_topic, json.dumps(payload))
        try:
            ParsedDeviceToServerStatusMessage(fake_message)
        except Exception as e:
            self.fail(f"Unexpected exception thrown when parsing good message")

    def test_missing_topic(self):

        status = {'key': 'val'}
        payload = {'device_id': 0,
                   'status': status
                   }

        fake_message = FakeRawMessage(None, json.dumps(payload))

        self.assertRaises(AttributeError, ParsedDeviceToServerStatusMessage, fake_message)

    def test_missing_payload(self):

        status = {'key': 'val'}
        payload = {'device_id': 0,
                   'status': status
                   }

        fake_message = FakeRawMessage(self.test_topic, None)

        self.assertRaises(AttributeError, ParsedDeviceToServerStatusMessage, fake_message)

    # TODO: finish build out
