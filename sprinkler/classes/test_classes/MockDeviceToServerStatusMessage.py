import json
from sprinkler.constants import COMMAND_TOPIC


class MockDeviceToServerStatusMessage:
    def __init__(self, device_id=None, status=None):

        self.topic = COMMAND_TOPIC
        payload = {}

        if device_id is not None:
            payload['device_id'] = device_id

        if status is not None:
            payload['status'] = status
        else:
            payload['status'] = {'voltage_ticks': 100, 'pressure_ticks': 100 }  #TODO: have an interface with this so we can set this how we want

        self.payload = json.dumps(payload)




