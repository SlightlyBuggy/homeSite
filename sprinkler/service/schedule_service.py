from sprinkler.models import IOTDeviceSchedule, ScheduleTypes, IOTDevice
from datetime import datetime, timezone
from sprinkler.service import command_service, device_service
import util.automation_utils as util


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

            device: IOTDevice = device_service.get_device_by_device_id(active_schedule.device.device_id)

            # handle each schedule type
            match active_schedule.schedule_type:
                case ScheduleTypes.SPRINKLE:
                    sprinkle_command_executed = command_service.handle_sprinkle_command(schedule=active_schedule,
                                                                                        device=device,
                                                                                        can_sprinkle=can_sprinkle)
                    if sprinkle_command_executed:
                        scheduled_tasks_executed += 1

                case _:
                    pass
    return scheduled_tasks_executed


def update_next_sprinkle_execution(schedule: IOTDeviceSchedule, device: IOTDevice):
    """
    Given a device and a schedule, update the next_execution property of the schedule
    :param schedule: IOTDeviceSchedule
    :param device: IOTDevice
    :return: None
    """

    current_dt = datetime.now(timezone.utc)
    # get the end time and status of watering event (rain, sprinkler, etc)
    last_water_end, watering_in_progress = util.get_last_watering_end_time_and_watering_status(
        device_id=device.device_id)

    # if a watering event is in progress, recalculate the next_execution starting now
    if watering_in_progress:
        schedule.next_execution = util.get_next_schd_using_start_time(schedule=schedule, starting_at=current_dt)
        schedule.save()
        return

    # we should ensure the next execution is after the last water event + schedule interval
    if last_water_end:
        tentative_next_execution = util.get_next_schd_using_start_time(schedule=schedule, starting_at=last_water_end)
        if tentative_next_execution > schedule.next_execution:
            schedule.next_execution = tentative_next_execution
            schedule.save()

        return


def update_sprinkle_schedules():
    all_sprinkle_schedules: list[IOTDeviceSchedule] = IOTDeviceSchedule.objects.filter(schedule_type=
                                                                                       ScheduleTypes.SPRINKLE)

    for sprinkle_schedule in all_sprinkle_schedules:
        update_next_sprinkle_execution(sprinkle_schedule, sprinkle_schedule.device)
