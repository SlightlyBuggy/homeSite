import datetime
import json
from .models import IOTDevice, IOTDeviceSchedule, ScheduleTypes

import util.automation_utils as util
import sprinkler.service.command_service as command_service
import sprinkler.service.weather_service as weather_service
import sprinkler.mqtt as mqtt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse


# TODO: make these get/post/put only as needed
def publish_message(request):
    # TODO: validate request body
    request_data = json.loads(request.body)

    mqtt_response = util.send_mqtt_message(request_data['topic'], request_data['body'])
    return mqtt_response


@require_http_methods(["GET"])
def test_device_command_status(request):
    request_data = json.loads(request.body)

    device_id = request_data['device_id']

    test_payload = {'device_id': device_id, 'command': mqtt.COMMAND_STATUS, 'body': {}}

    mqtt_response = util.send_mqtt_message(mqtt.COMMAND_TOPIC, str(test_payload))
    return mqtt_response


def test_device_command_sprinkle_start(request):
    request_data = json.loads(request.body)

    device_id = request_data['device_id']

    test_payload = {
        'device_id': device_id,
        'command': mqtt.COMMAND_SPRINKLE_START,
        'body': {

        }
    }

    # add request params
    if 'watering_length_minutes' in request_data:
        test_payload['body']['watering_length_minutes'] = request_data['watering_length_minutes']

    if 'watering_length_seconds' in request_data:
        test_payload['body']['watering_length_seconds'] = request_data['watering_length_seconds']

    mqtt_response = util.send_mqtt_message(mqtt.COMMAND_TOPIC, str(test_payload))
    return mqtt_response


def get_precip_observations(request):
    precip_observations = weather_service.get_precip_observations(test=True)
    print("Fetched test precipitation report")
    print(precip_observations)

    return JsonResponse({'precip_events': precip_observations.precip_events})


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
