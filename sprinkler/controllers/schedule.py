from sprinkler.models import IOTDeviceSchedule, ScheduleTypes, IOTDevice
from datetime import datetime, timezone
from sprinkler.service import command_service, device_service
from django.http import JsonResponse


# TODO: should the device status be part of the scheduling system?
def ping_devices_for_status(request):
    """
    This endpoint fetches device statusus for each device.  This triggers scheduled task execution when each device
    reports in
    :param request:
    :return: None
    """

    # grab active schedules
    active_schedules: list[IOTDeviceSchedule] = IOTDeviceSchedule.objects.filter(active=True)
    current_dt = datetime.now(timezone.utc)

    scheduled_tasks_executed = 0

    for active_schedule in active_schedules:

        # check if schedule should be executed now
        if active_schedule.next_execution <= current_dt:

            device: IOTDevice = IOTDevice.objects.get(pk=active_schedule.device.id)

            # handle each schedule type
            match active_schedule.schedule_type:
                case ScheduleTypes.GET_DEVICE_STATUS:
                    if device_service.should_device_be_awake(device):
                        command_service.handle_status_command(schedule=active_schedule, device=device)
                        scheduled_tasks_executed += 1

                case _:
                    print(f"Unhandled schedule type {active_schedule.schedule_type}")
    print(f"{current_dt}: Executed {scheduled_tasks_executed} tasks")
    return JsonResponse({'tasks executed': scheduled_tasks_executed})
