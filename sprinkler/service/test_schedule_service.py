from django.test import TestCase
from sprinkler.models import ScheduleTypes, IOTDevice, IOTDeviceSchedule, IOTDeviceScheduleExecution, RainLog
from sprinkler.factories import iotdevice_factory, iotdeviceschedule_factory, rainlog_factory
from datetime import datetime, timedelta, timezone
from sprinkler.service import schedule_service


class ScheduleServiceTest(TestCase):

    test_device: IOTDevice
    now: datetime
    one_hour_ago: datetime
    one_hour_from_now: datetime

    def setUp(self):
        self.test_device = iotdevice_factory.create_device()

        self.now = datetime.now(timezone.utc)
        self.one_hour_ago = self.now + timedelta(hours=-1)
        self.one_hour_from_now = self.now + timedelta(hours=1)

    def test_execute_scheduled_task_past_can_sprinkle(self):

        # make a schedule one hour in the past
        test_schedule = iotdeviceschedule_factory.create_weekly_sprinkle_schedule(device=self.test_device,
                                                                                  next_execution=self.one_hour_ago)

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
        test_schedule = iotdeviceschedule_factory.create_weekly_sprinkle_schedule(device=self.test_device,
                                                                                  next_execution=self.one_hour_ago)

        executed_tasks = schedule_service.execute_scheduled_tasks(device=self.test_device, can_sprinkle=False)

        # since we said the device cannot sprinkle, no tasks should be executed
        self.assertEquals(executed_tasks, 0)

        # the db should have no recorded executed tasks
        test_device_schedule_executions: list[IOTDeviceScheduleExecution] = \
            IOTDeviceScheduleExecution.objects.filter(iot_device_schedule=test_schedule)
        self.assertEquals(len(test_device_schedule_executions), 0)

    def test_execute_scheduled_tasks_future_can_sprinkle(self):

        # make a schedule one hour in the future
        test_schedule = iotdeviceschedule_factory.create_weekly_sprinkle_schedule(device=self.test_device,
                                                                                  next_execution=self.one_hour_from_now)

        executed_tasks = schedule_service.execute_scheduled_tasks(device=self.test_device, can_sprinkle=True)

        # since the scheduled time is in the future, no tasks should be executed
        self.assertEquals(executed_tasks, 0)

        # the db should have no recorded executed tasks
        test_device_schedule_executions: list[IOTDeviceScheduleExecution] = \
            IOTDeviceScheduleExecution.objects.filter(iot_device_schedule=test_schedule)
        self.assertEquals(len(test_device_schedule_executions), 0)

    def test_execute_scheduled_tasks_future_cannot_sprinkle(self):

        # make a schedule one hour in the future
        test_schedule = iotdeviceschedule_factory.create_weekly_sprinkle_schedule(device=self.test_device,
                                                                                  next_execution=self.one_hour_from_now)

        executed_tasks = schedule_service.execute_scheduled_tasks(device=self.test_device, can_sprinkle=False)

        # since the scheduled time is in the future, and we said no sprinkling allowed, no tasks should be executed
        self.assertEquals(executed_tasks, 0)

        # the db should have no recorded executed tasks
        test_device_schedule_executions: list[IOTDeviceScheduleExecution] = \
            IOTDeviceScheduleExecution.objects.filter(iot_device_schedule=test_schedule)
        self.assertEquals(len(test_device_schedule_executions), 0)

    def test_update_next_sprinkle_execution_no_change(self):
        iotdeviceschedule_factory.create_weekly_sprinkle_schedule(device=self.test_device,
                                                                  next_execution=self.one_hour_from_now)

        schedule_service.update_sprinkle_schedules()

        test_schedule : IOTDeviceSchedule = IOTDeviceSchedule.objects.filter(device=self.test_device)[0]

        self.assertEquals(self.one_hour_from_now, test_schedule.next_execution)

    def test_update_next_sprinkle_execution_water_in_progress(self):
        iotdeviceschedule_factory.create_weekly_sprinkle_schedule(device=self.test_device,
                                                                  next_execution=self.one_hour_ago)

        rainlog_factory.create_rain_log_in_progress()

        schedule_service.update_sprinkle_schedules()

        test_schedule: IOTDeviceSchedule = IOTDeviceSchedule.objects.filter(device=self.test_device)[0]

        # the new execution should have been calculated from the current time and use the full interval
        interval_hours = test_schedule.minimum_hours_between_executions

        # create bounding for the next execution.  the schedule service ensures the minimum interval is always respected
        # and will push the schedule forward by a day if needed to achieve that
        now = datetime.now(tz=timezone.utc)
        min_dt_of_next_execution = now + timedelta(hours=interval_hours)
        min_dt_of_next_execution.replace(hour=0, minute=0)

        max_dt_of_next_execution = now + timedelta(hours=interval_hours + 24)
        max_dt_of_next_execution.replace(hour=0, minute=0)

        self.assertTrue(test_schedule.next_execution >= min_dt_of_next_execution)
        self.assertTrue(test_schedule.next_execution <= max_dt_of_next_execution)

    def test_update_next_sprinkle_execution_water_finished_one_hour_ago(self):

        iotdeviceschedule_factory.create_weekly_sprinkle_schedule(device=self.test_device,
                                                                  next_execution=self.one_hour_from_now)

        rainlog_factory.create_rain_log_finished_one_hour_ago()

        schedule_service.update_sprinkle_schedules()

        test_schedule: IOTDeviceSchedule = IOTDeviceSchedule.objects.filter(device=self.test_device)[0]

        # the new execution should have been calculated from the current time and use the full interval
        interval_hours = test_schedule.minimum_hours_between_executions

        # create bounding for the next execution.  the schedule service ensures the minimum interval is always respected
        # and will push the schedule forward by a day if needed to achieve that
        now = datetime.now(tz=timezone.utc)
        min_dt_of_next_execution = now + timedelta(hours=interval_hours - 1)
        min_dt_of_next_execution.replace(hour=0, minute=0)

        max_dt_of_next_execution = now + timedelta(hours=interval_hours + 23)
        max_dt_of_next_execution.replace(hour=0, minute=0)

        self.assertTrue(test_schedule.next_execution >= min_dt_of_next_execution)
        self.assertTrue(test_schedule.next_execution <= max_dt_of_next_execution)




