from django.test import TestCase
from sprinkler.service import device_service
from sprinkler.models import IOTDevice, IOTDeviceSchedule, SprinklerLog, ScheduleTypes, DeviceStatusLog
from datetime import datetime, timezone, timedelta
import ast
from sprinkler import constants


class DeviceServiceTest(TestCase):
    test_device = None
    last_message_body_dict = None
    last_message_topic = None
    fake_device_low_pressure_ticks = 50
    fake_device_high_pressure_ticks = 100
    test_device_id = 0

    def fake_mqtt_message_sender(self, topic, body):
        print(f"Sending message {body} on topic {topic}")
        self.last_message_body_dict = ast.literal_eval(body)
        self.last_message_topic = topic

    @staticmethod
    def get_ticks_from_percentage_of_cal_range(percentage, cal_low, cal_high):
        cal_range = cal_high - cal_low
        ticks = percentage * cal_range / 100 + cal_low
        return ticks

    def setUp(self):

        # create a device
        self.test_device = IOTDevice.objects.create(name="test1",
                                                    minimum_water_interval_hours=168,
                                                    watering_length_minutes=10,
                                                    watering_wait_minutes=5,
                                                    watering_repetitions=2,
                                                    device_id=self.test_device_id,
                                                    cal_low_ticks_voltage=100,
                                                    cal_high_ticks_voltage=700,
                                                    cal_low_voltage=10,
                                                    cal_high_voltage=13,
                                                    cal_low_pressure_ticks=self.fake_device_low_pressure_ticks,
                                                    cal_high_pressure_ticks=self.fake_device_high_pressure_ticks,
                                                    ipv4_address=1,
                                                    port=1)

    def test_handle_device_status_executes_scheduled_event_in_past(self):
        test_status = {
            'voltage_ticks': 50,
            'pressure_ticks': 100
        }

        # create a sprinkle event that's in the past
        one_hour_ago = datetime.now(timezone.utc) + timedelta(hours=-1)

        IOTDeviceSchedule.objects.create(device=self.test_device,
                                         hour=0,
                                         minute=0,
                                         next_execution=one_hour_ago,
                                         active=True,
                                         interval_minutes=0,
                                         schedule_type=ScheduleTypes.SPRINKLE)

        device_service.handle_device_status(0, test_status, self.fake_mqtt_message_sender)

        sprinkler_log_qs = SprinklerLog.objects.filter(device__device_id=0)
        self.assertTrue(sprinkler_log_qs.exists())

    def test_handle_device_status_sleep_for_scheduled_event_in_future(self):
        test_status = {
            'voltage_ticks': 50,
            'pressure_ticks': 100
        }

        # create a sprinkle event that's in the future
        one_hour_ago = datetime.now(timezone.utc) + timedelta(hours=1)

        IOTDeviceSchedule.objects.create(device=self.test_device,
                                         hour=0,
                                         minute=0,
                                         next_execution=one_hour_ago,
                                         active=True,
                                         interval_minutes=0,
                                         schedule_type=ScheduleTypes.SPRINKLE)

        device_service.handle_device_status(0, test_status, self.fake_mqtt_message_sender)

        self.assertEqual('command', self.last_message_topic)
        self.assertEqual('sleep_now', self.last_message_body_dict['command'])

    def test_handle_device_status_power_off_if_no_schedules_today(self):
        test_status = {
            'voltage_ticks': 50,
            'pressure_ticks': 100
        }

        # create a sprinkle event that's in the future
        one_hour_ago = datetime.now(timezone.utc) + timedelta(days=2)

        IOTDeviceSchedule.objects.create(device=self.test_device,
                                         hour=0,
                                         minute=0,
                                         next_execution=one_hour_ago,
                                         active=True,
                                         interval_minutes=0,
                                         schedule_type=ScheduleTypes.SPRINKLE)

        device_service.handle_device_status(device_id=0, status=test_status,
                                            message_sender=self.fake_mqtt_message_sender)

        self.assertEqual('command', self.last_message_topic)
        self.assertEqual('power_off', self.last_message_body_dict['command'])

    def test_enough_water_to_sprinkle_on_threshold(self):

        test_device: IOTDevice = IOTDevice.objects.filter(device_id=self.test_device_id)[0]

        threshold_ticks = self.get_ticks_from_percentage_of_cal_range(constants.MIN_PERCENT_TO_WATER,
                                                                      test_device.cal_low_pressure_ticks,
                                                                      test_device.cal_high_pressure_ticks)

        DeviceStatusLog.objects.create(device=self.test_device, supply_voltage_ticks=500, supply_voltage=12.5,
                                       water_pressure_ticks=threshold_ticks)

        enough_water = device_service.device_measured_enough_water_to_sprinkle_from_last_status(device=self.test_device)

        self.assertTrue(enough_water)

    def test_enough_water_to_sprinkle_has_enough_in_range(self):
        test_device: IOTDevice = IOTDevice.objects.filter(device_id=self.test_device_id)[0]

        threshold_ticks = self.get_ticks_from_percentage_of_cal_range(constants.MIN_PERCENT_TO_WATER,
                                                                      test_device.cal_low_pressure_ticks,
                                                                      test_device.cal_high_pressure_ticks)

        ticks_to_test = threshold_ticks + 1

        DeviceStatusLog.objects.create(device=self.test_device, supply_voltage_ticks=500, supply_voltage=12.5,
                                       water_pressure_ticks=ticks_to_test)

        enough_water = device_service.device_measured_enough_water_to_sprinkle_from_last_status(device=self.test_device)

        self.assertTrue(enough_water)

    def test_enough_water_to_sprinkle_not_enough_in_range(self):

        test_device: IOTDevice = IOTDevice.objects.filter(device_id=self.test_device_id)[0]

        threshold_ticks = self.get_ticks_from_percentage_of_cal_range(constants.MIN_PERCENT_TO_WATER,
                                                                      test_device.cal_low_pressure_ticks,
                                                                      test_device.cal_high_pressure_ticks)

        ticks_to_test = threshold_ticks - 1
        DeviceStatusLog.objects.create(device=self.test_device, supply_voltage_ticks=500, supply_voltage=12.5,
                                       water_pressure_ticks=ticks_to_test)

        enough_water = device_service.device_measured_enough_water_to_sprinkle_from_last_status(device=self.test_device)

        self.assertFalse(enough_water)

    def test_enough_water_to_sprinkle_not_enough_out_of_range(self):
        test_device: IOTDevice = IOTDevice.objects.filter(device_id=self.test_device_id)[0]

        ticks_to_test = test_device.cal_low_pressure_ticks - 1

        DeviceStatusLog.objects.create(device=self.test_device, supply_voltage_ticks=500, supply_voltage=12.5,
                                       water_pressure_ticks=ticks_to_test)

        enough_water = device_service.device_measured_enough_water_to_sprinkle_from_last_status(device=self.test_device)

        self.assertFalse(enough_water)

    def test_enough_water_to_sprinkle_has_enough_out_of_range(self):
        test_device: IOTDevice = IOTDevice.objects.filter(device_id=self.test_device_id)[0]

        ticks_to_test = test_device.cal_high_pressure_ticks + 1

        DeviceStatusLog.objects.create(device=self.test_device, supply_voltage_ticks=500, supply_voltage=12.5,
                                       water_pressure_ticks=ticks_to_test)

        enough_water = device_service.device_measured_enough_water_to_sprinkle_from_last_status(device=self.test_device)

        self.assertTrue(enough_water)

