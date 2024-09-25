from sprinkler.models import IOTDeviceSchedule, IOTDevice, ScheduleTypes
from datetime import datetime


def create_schedule_zero_hour_minute(device: IOTDevice, next_execution: datetime,
                                     schedule_type) -> IOTDeviceSchedule:

    schedule = IOTDeviceSchedule.objects.create(device=device,
                                                hour=0,
                                                minute=0,
                                                next_execution=next_execution,
                                                active=True,
                                                interval_minutes=0,
                                                schedule_type=schedule_type)

    return schedule


def create_sprinkle_schedule(device: IOTDevice, next_execution: datetime) -> IOTDeviceSchedule:

    return create_schedule_zero_hour_minute(device=device, next_execution=next_execution,
                                            schedule_type=ScheduleTypes.SPRINKLE)

