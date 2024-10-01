class RawDeviceToServerStatusMessage:
    def __init__(self, topic, device_id=None, status=None):

        self.topic = topic
        payload = {}

        if device_id:
            payload['device_id'] = device_id

        if status:
            payload['status'] = status
        else:
            payload['status'] = {'voltage_ticks': 100, 'pressure_ticks': 100 }  #TODO: have an interface with this so we can set this how we want

        self.payload = str(payload)

