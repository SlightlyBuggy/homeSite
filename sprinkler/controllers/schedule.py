from sprinkler.models import IOTDeviceSchedule, ScheduleTypes, IOTDevice
from datetime import datetime, timezone
from sprinkler.service import command_service
from django.http import JsonResponse


def execute_scheduled_tasks(request):
    """
    This endpoint looks at the list of active IOTDeviceSchedules and determines what to do with each.  A
    IOTDeviceScheduleExecution is created whenever scheduled tasks are executed
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
                    command_service.handle_status_command(schedule=active_schedule, device=device)
                    scheduled_tasks_executed += 1

                case ScheduleTypes.SPRINKLE:
                    command_service.handle_sprinkle_command(schedule=active_schedule, device=device)
                    scheduled_tasks_executed += 1

                case _:
                    print(f"Unhandled schedule type {active_schedule.schedule_type}")
    print(f"{current_dt}: Executed {scheduled_tasks_executed} tasks")
    return JsonResponse({'tasks executed': scheduled_tasks_executed})
