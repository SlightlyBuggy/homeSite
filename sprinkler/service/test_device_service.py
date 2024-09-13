from django.test import TestCase
from sprinkler.service import device_service
from sprinkler.models import IOTDevice, IOTDeviceSchedule, SprinklerLog
from datetime import datetime, timezone, timedelta


class DeviceServiceTest(TestCase):

    def setUp(self):

        # create a device
        test_device_id = 0
        test_device = IOTDevice.objects.create(name="test1",
                                               minimum_water_interval_hours=168,
                                               watering_length_minutes=10,
                                               watering_wait_minutes=5,
                                               watering_repetitions=2,
                                               device_id=test_device_id,
                                               cal_low_ticks_voltage=486,
                                               cal_high_ticks_voltage=679,
                                               cal_low_voltage=10,
                                               cal_high_voltage=13,
                                               cal_low_pressure_ticks=75,
                                               cal_high_pressure_ticks=105,
                                               ipv4_address=1,
                                               port=1)

        # create a sprinkle event that's in the past
        one_hour_ago = datetime.now(timezone.utc) + timedelta(hours=-1)

        IOTDeviceSchedule.objects.create(device=test_device,
                                         hour=0,
                                         minute=0,
                                         next_execution=one_hour_ago,
                                         active=True,
                                         interval_minutes=0)

    def test_handle_device_status(self):
        test_status = {
            'voltage_ticks': 50,
            'pressure_ticks': 100
        }

        device_service.handle_device_status(0, test_status, None)

        sprinkler_log_qs = SprinklerLog.objects.filter(device__device_id=0)
        self.assertTrue(sprinkler_log_qs.exists())
