from sprinkler.models import IOTDeviceSchedule, IOTDevice, ScheduleTypes
from datetime import datetime


def create_schedule_zero_hour_minute(device: IOTDevice, next_execution: datetime,
                                     schedule_type: ScheduleTypes,
                                     minimum_hours_between_executions: int) -> IOTDeviceSchedule:

    schedule = IOTDeviceSchedule.objects.create(device=device,
                                                hour=0,
                                                minute=0,
                                                next_execution=next_execution,
                                                active=True,
                                                schedule_type=schedule_type,
                                                minimum_hours_between_executions=minimum_hours_between_executions)

    return schedule


def create_weekly_sprinkle_schedule(device: IOTDevice, next_execution: datetime) -> IOTDeviceSchedule:

    return create_schedule_zero_hour_minute(device=device, next_execution=next_execution,
                                            schedule_type=ScheduleTypes.SPRINKLE, minimum_hours_between_executions=168)

