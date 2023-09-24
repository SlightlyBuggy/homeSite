from sprinkler.models import IOTDeviceSchedule, ScheduleTypes, IOTDevice
from datetime import datetime, timezone
from sprinkler.service import command_service, schedule_service
from django.http import JsonResponse


# TODO: should the device status be part of the scheduling system?
def ping_devices_for_status_and_update_schedules(request):
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
        # TODO: this is a filthy hack.  Need to have a separate processes that need to run immediately from schedules
        if active_schedule.next_execution <= current_dt or active_schedule.schedule_type == ScheduleTypes.SPRINKLE:

            device: IOTDevice = IOTDevice.objects.get(pk=active_schedule.device.id)

            # handle each schedule type
            match active_schedule.schedule_type:

                # ping the device for status if it is supposed to be awake
                case ScheduleTypes.GET_DEVICE_STATUS:
                    if device.should_be_awake():
                        command_service.handle_status_command(schedule=active_schedule, device=device)
                        scheduled_tasks_executed += 1

                # for the sprinkle command, we just want to ensure next_exection is appropriate based on
                # past water events and rain events
                case ScheduleTypes.SPRINKLE:
                    schedule_service.update_next_sprinkle_execution(schedule=active_schedule, device=device)

                case _:
                    pass

    return JsonResponse({'tasks executed': scheduled_tasks_executed})
