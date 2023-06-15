import datetime
import json
from .models import IOTDevice, IOTDeviceSchedule, ScheduleTypes

import homeAutomation.util.automation_utils as util
import homeAutomation.service.command_service as command_service
import homeAutomation.mqtt as mqtt
from django.views.decorators.http import require_http_methods


# TODO: make these get/post/put only as needed
def publish_message(request):
    # TODO: validate request body
    request_data = json.loads(request.body)

    mqtt_response = util.send_mqtt_message(request_data['topic'], request_data['body'])
    return mqtt_response


@require_http_methods(["GET"])
def test_device_command_status(request):

    test_payload = {'device_id': 0, 'command': mqtt.COMMAND_STATUS, 'body': {}}

    mqtt_response = util.send_mqtt_message(mqtt.COMMAND_TOPIC, str(test_payload))
    return mqtt_response


def test_device_command_sprinkle_start(request):
    test_payload = {
        'device_id': '0',
        'command': mqtt.COMMAND_SPRINKLE_START,
        'body': {
            'watering_length_minutes': 1,
            'watering_wait_minutes': 1,
            'watering_repetitions': 2,
        }
    }
    mqtt_response = util.send_mqtt_message(mqtt.COMMAND_TOPIC, str(test_payload))
    return mqtt_response


def execute_scheduled_tasks(request):
    """
    This endpoint looks at the list of active IOTDeviceSchedules and determines what to do with each.  A
    IOTDeviceScheduleExecution is created whenever scheduled tasks are executed
    :param request:
    :return: None
    """

    # grab active schedules
    active_schedules: list[IOTDeviceSchedule] = IOTDeviceSchedule.objects.filter(active=True)
    current_dt = datetime.datetime.now()

    for active_schedule in active_schedules:

        # check if schedule should be executed now
        if active_schedule.next_execution <= current_dt:

            device: IOTDevice = IOTDevice.objects.get(pk=active_schedule.device_id)

            # handle each schedule type
            match active_schedule.schedule_type:
                case ScheduleTypes.GET_DEVICE_STATUS:
                    command_service.handle_status_command(schedule=active_schedule, device=device)

                case ScheduleTypes.SPRINKLE:
                    command_service.handle_sprinkle_command(schedule=active_schedule, device=device)

                case _:
                    print(f"Unhandled schedule type {active_schedule.schedule_type}")
