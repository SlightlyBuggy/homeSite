from sprinkler.models import IOTDevice
from sprinkler.service import device_service


class DeviceStatus:

    def __init__(self, device_id, status_dict):

        self.device_id = device_id
        self.status_dict = status_dict

        self.voltage_ticks: int | None = None
        self.voltage: float | None = None
        self.water_pressure_ticks: int | None = None

        self._parse_status_dict()
        self._calculate_voltage_from_status()

    def _parse_status_dict(self):

        try:
            self.voltage_ticks = self.status_dict['voltage_ticks']
        except KeyError:
            raise KeyError(f"Status dict does not have 'voltage_ticks' key: {self.status_dict}")

        try:
            self.water_pressure_ticks = self.status_dict['pressure_ticks']
        except KeyError:
            raise KeyError(f"Status dict does not have 'pressure_ticks' key: {self.status_dict}")

    def _calculate_voltage_from_status(self):

        device: IOTDevice = device_service.get_device_by_id(self.device_id)

        if not device:
            raise Exception(f"Device with id {self.device_id} not found")

        self.voltage = device.get_voltage_from_voltage_ticks(self.voltage_ticks)
