from django.test import TestCase
from sprinkler.models import ScheduleTypes, IOTDevice, IOTDeviceScheduleExecution, IOTDeviceSchedule, IOTDeviceScheduleExecution
from sprinkler.factories import iotdevice_factory, iotdeviceschedule_factory
from datetime import datetime, timedelta, timezone
from sprinkler.service import schedule_service


class ScheduleServiceTest(TestCase):

    test_device: IOTDevice

    def setUp(self):
        self.test_device = iotdevice_factory.create_device()

    def test_execute_scheduled_task_past_can_sprinkle(self):

        # make a schedule one hour in the past
        now = datetime.now(timezone.utc)
        one_hour_ago = now + timedelta(hours=-1)
        test_schedule = iotdeviceschedule_factory.create_sprinkle_schedule(device=self.test_device,
                                                                           next_execution=one_hour_ago)

        executed_tasks = schedule_service.execute_scheduled_tasks(device=self.test_device, can_sprinkle=True)
        self.assertEquals(executed_tasks, 1)

        test_device_schedule_executions: list[IOTDeviceScheduleExecution] = \
            IOTDeviceScheduleExecution.objects.filter(iot_device_schedule=test_schedule)
        self.assertEquals(len(test_device_schedule_executions), 1)

        execution: IOTDeviceScheduleExecution = test_device_schedule_executions[0]
        self.assertEqual(execution.schedule_type, ScheduleTypes.SPRINKLE)

    def test_execute_scheduled_tasks_past_cannot_sprinkle(self):
        pass

    def test_execute_scheduled_tasks_future_can_sprinkle(self):
        pass

    def test_execute_scheduled_tasks_future_cannot_sprinkle(self):
        pass

    # TODO: tests for get_today_scheduled_tasks and update_next_sprinkle_execution


