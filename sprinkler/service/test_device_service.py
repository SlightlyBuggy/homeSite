from django.test import TestCase
from sprinkler.service import device_service
from sprinkler.models import IOTDevice, IOTDeviceSchedule, SprinklerLog, ScheduleTypes
from datetime import datetime, timezone, timedelta
import ast


class DeviceServiceTest(TestCase):
    test_device = None
    last_message_body_dict = None
    last_message_topic = None

    def fake_mqtt_message_sender(self, topic, body):
        print(f"Sending message {body} on topic {topic}")
        self.last_message_body_dict = ast.literal_eval(body)
        self.last_message_topic = topic

    def setUp(self):

        # create a device
        test_device_id = 0
        self.test_device = IOTDevice.objects.create(name="test1",
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

        # TODO: need to look at what command was actually sent
        device_service.handle_device_status(0, test_status, self.fake_mqtt_message_sender)

        self.assertEqual('command', self.last_message_topic)
        self.assertEqual('power_off', self.last_message_body_dict['command'])
