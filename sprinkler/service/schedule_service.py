from sprinkler.models import IOTDeviceSchedule, ScheduleTypes, IOTDevice
from datetime import datetime, timezone
from sprinkler.service import command_service
from django.http import JsonResponse
import util.automation_utils as util
from typing import List


def execute_scheduled_tasks(device: IOTDevice, can_sprinkle):
    """
    Execute scheduled tasks for a particular device
    :param device: IOTDevice
    :param can_sprinkle: boolean, determines whether device can execute a sprinkling task
    :return: int: num of tasks executed
    """
    # grab active schedules
    active_schedules: list[IOTDeviceSchedule] = IOTDeviceSchedule.objects.filter(active=True, device=device)
    current_dt = datetime.now(timezone.utc)

    scheduled_tasks_executed = 0

    for active_schedule in active_schedules:

        # check if schedule should be executed now
        if active_schedule.next_execution <= current_dt:

            device: IOTDevice = IOTDevice.objects.get(pk=active_schedule.device.id)

            # handle each schedule type
            match active_schedule.schedule_type:
                case ScheduleTypes.SPRINKLE:
                    command_service.handle_sprinkle_command(schedule=active_schedule, device=device,
                                                            can_sprinkle=can_sprinkle)
                    scheduled_tasks_executed += 1

                case _:
                    pass
    return scheduled_tasks_executed


def get_today_scheduled_tasks(device: IOTDevice) -> List[IOTDeviceSchedule]:
    """
    Given an IOTDevice, fetch the scheduled tasks for today

    :param device: IOTDevice
    :return: List of scheduled tasks that need to be executed today
    """
    active_schedules: list[IOTDeviceSchedule] = IOTDeviceSchedule.objects.filter(active=True, device=device)

    current_dt = datetime.now(timezone.utc)
    current_date = current_dt.date()

    today_schedules = [schedule for schedule in active_schedules if schedule.next_execution.date() == current_date]

    return today_schedules


def update_next_sprinkle_execution(schedule: IOTDeviceSchedule, device: IOTDevice):
    """
    Given a device and a schedule, update the next_execution property of the schedule
    :param schedule: IOTDeviceSchedule
    :param device: IOTDevice
    :return: None
    """

    current_dt = datetime.now(timezone.utc)
    # get the end time and status of watering event (rain, sprinkler, etc)
    last_water_end, watering_in_progress = util.get_last_watering_end_time_and_watering_status(device_id=device.device_id)

    # if a watering event is in progress, recalculate the next_execution starting now
    if watering_in_progress:
        schedule.next_execution = util.get_next_schd_using_start_time(schedule=schedule, starting_at=current_dt,
                                                                      interval_minutes=
                                                                      device.minimum_water_interval_hours*60)
        schedule.save()
        return

    # we should ensure the next execution is after the last water event + schedule interval
    if last_water_end:
        tentative_next_exeuction = util.get_next_schd_using_start_time(schedule=schedule, starting_at=last_water_end,
                                                                       interval_minutes=
                                                                       device.minimum_water_interval_hours*60)
        if tentative_next_exeuction > schedule.next_execution:
            schedule.next_execution = tentative_next_exeuction
            schedule.save()

        return


def update_sprinkle_schedules():
    all_sprinkle_schedules: list[IOTDeviceSchedule] = IOTDeviceSchedule.objects.filter(schedule_type=ScheduleTypes.SPRINKLE)

    for sprinkle_schedule in all_sprinkle_schedules:
        update_next_sprinkle_execution(sprinkle_schedule, sprinkle_schedule.device)
