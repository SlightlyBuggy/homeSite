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

        # since we said the device can sprinkle and the scheduled time is in the past, there should be one execution
        self.assertEquals(executed_tasks, 1)

        # the db should record that single execution
        test_device_schedule_executions: list[IOTDeviceScheduleExecution] = \
            IOTDeviceScheduleExecution.objects.filter(iot_device_schedule=test_schedule)
        self.assertEquals(len(test_device_schedule_executions), 1)

        # the execution should be of the correct type
        execution: IOTDeviceScheduleExecution = test_device_schedule_executions[0]
        self.assertEqual(execution.schedule_type, ScheduleTypes.SPRINKLE)

    def test_execute_scheduled_tasks_past_cannot_sprinkle(self):

        # make a schedule one hour in the past
        now = datetime.now(timezone.utc)
        one_hour_ago = now + timedelta(hours=-1)
        test_schedule = iotdeviceschedule_factory.create_sprinkle_schedule(device=self.test_device,
                                                                           next_execution=one_hour_ago)

        executed_tasks = schedule_service.execute_scheduled_tasks(device=self.test_device, can_sprinkle=False)

        # since we said the device cannot sprinkle, no tasks should be executed
        self.assertEquals(executed_tasks, 0)

        # the db should have no recorded executed tasks
        test_device_schedule_executions: list[IOTDeviceScheduleExecution] = \
            IOTDeviceScheduleExecution.objects.filter(iot_device_schedule=test_schedule)
        self.assertEquals(len(test_device_schedule_executions), 0)

    def test_execute_scheduled_tasks_future_can_sprinkle(self):

        # make a schedule one hour in the future
        now = datetime.now(timezone.utc)
        one_hour_ago = now + timedelta(hours=1)
        test_schedule = iotdeviceschedule_factory.create_sprinkle_schedule(device=self.test_device,
                                                                           next_execution=one_hour_ago)

        executed_tasks = schedule_service.execute_scheduled_tasks(device=self.test_device, can_sprinkle=True)

        # since the scheduled time is in the future, no tasks should be executed
        self.assertEquals(executed_tasks, 0)

        # the db should have no recorded executed tasks
        test_device_schedule_executions: list[IOTDeviceScheduleExecution] = \
            IOTDeviceScheduleExecution.objects.filter(iot_device_schedule=test_schedule)
        self.assertEquals(len(test_device_schedule_executions), 0)

    def test_execute_scheduled_tasks_future_cannot_sprinkle(self):

        # make a schedule one hour in the future
        now = datetime.now(timezone.utc)
        one_hour_from_now = now + timedelta(hours=1)
        test_schedule = iotdeviceschedule_factory.create_sprinkle_schedule(device=self.test_device,
                                                                           next_execution=one_hour_from_now)

        executed_tasks = schedule_service.execute_scheduled_tasks(device=self.test_device, can_sprinkle=False)

        # since the scheduled time is in the future, and we said no sprinkling allowed, no tasks should be executed
        self.assertEquals(executed_tasks, 0)

        # the db should have no recorded executed tasks
        test_device_schedule_executions: list[IOTDeviceScheduleExecution] = \
            IOTDeviceScheduleExecution.objects.filter(iot_device_schedule=test_schedule)
        self.assertEquals(len(test_device_schedule_executions), 0)

    # TODO: tests for get_today_scheduled_tasks and update_next_sprinkle_execution


