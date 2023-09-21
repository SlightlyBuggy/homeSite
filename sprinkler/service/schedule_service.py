from sprinkler.models import IOTDeviceSchedule, ScheduleTypes, IOTDevice
from datetime import datetime, timezone
from sprinkler.service import command_service
from django.http import JsonResponse


# TODO: consider how to best ensure devices actually get the message.  If there's just a scheduling system, a device might
# be asleep, which is why this is being called when a device checks in.  Perhaps the only thing handled by the schedule
# endpoint should be the status ping
def execute_scheduled_tasks(device: IOTDevice):
    """
    Execute scheduled tasks for a particular device
    :param device:
    :return:
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
                # case ScheduleTypes.GET_DEVICE_STATUS:
                #     command_service.handle_status_command(schedule=active_schedule, device=device)
                #     scheduled_tasks_executed += 1

                case ScheduleTypes.SPRINKLE:
                    command_service.handle_sprinkle_command(schedule=active_schedule, device=device)
                    scheduled_tasks_executed += 1

                case _:
                    print(f"Unhandled schedule type {active_schedule.schedule_type}")
    print(f"{current_dt}: Executed {scheduled_tasks_executed} tasks")
    return JsonResponse({'tasks executed': scheduled_tasks_executed})