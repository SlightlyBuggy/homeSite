from sprinkler.models import IOTDeviceSchedule, ScheduleTypes, IOTDevice
from datetime import datetime, timezone
from sprinkler.service import command_service, schedule_service
from django.http import JsonResponse


# TODO: break this into separate things.  there should be two funtions: that one pings all known devices for status,
# and the other that updates schedules.  The former will catch any devices that are online and waiting
def ping_devices_for_status(request):
    """
    This endpoint asks each device to report status

    :param request:
    :return: None
    """

    devices: list[IOTDevice] = IOTDevice.objects.all()

    for device in devices:
        command_service.handle_status_command(device=device)

    return


def update_schedules(request):
    """
    This endpoint fetches device statusus for each device.  This triggers scheduled task execution when each device
    reports in
    :param request:
    :return: None
    """

    # grab active schedules
    active_schedules: list[IOTDeviceSchedule] = IOTDeviceSchedule.objects.filter(active=True)
    current_dt = datetime.now(timezone.utc)

    for active_schedule in active_schedules:

        # if the next execution time is in the past, we need to bump it out
        if active_schedule.next_execution <= current_dt:

            device: IOTDevice = IOTDevice.objects.get(pk=active_schedule.device.id)

            # handle each schedule type
            match active_schedule.schedule_type:

                case ScheduleTypes.SPRINKLE:
                    schedule_service.update_next_sprinkle_execution(schedule=active_schedule, device=device)

                case _:
                    pass

    return JsonResponse({'updated schedules'})
