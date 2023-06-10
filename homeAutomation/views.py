import datetime
import json
from django.http import JsonResponse
from .mqtt import client as mqtt_client
from .models import IOTDevice, IOTDeviceSchedule, IOTDeviceScheduleExecution, ScheduleTypes
from util import automation_utils


def publish_message(request):
    # TODO: validate request body
    request_data = json.loads(request.body)

    mqtt_response = automation_utils.send_mqtt_message(request_data['topic'], request_data['body'])
    return mqtt_response


def test_device_message(request):

    mqtt_response = automation_utils.send_mqtt_message('device_messages', 'test device message sent')
    return mqtt_response


def test_device_command(request):

    mqtt_response = automation_utils.send_mqtt_message('device_commands', 'test device command sent')
    return mqtt_response


def execute_scheduled_tasks(request):

    # grab active schedules
    active_schedules: list[IOTDeviceSchedule] = IOTDeviceSchedule.objects.filter(active=True)
    current_dt = datetime.datetime.now()

    for active_schedule in active_schedules:

        # check if schedule should be executed now
        if active_schedule.next_execution <= current_dt:

            device: IOTDevice = IOTDevice.objects.get(pk=active_schedule.device)
            device_id = device.id

            match active_schedule.schedule_type:
                case ScheduleTypes.GET_DEVICE_STATUS:

                    status_body = {
                                    'device_id': device_id,
                                    'message': 'status',
                                    'message_body': None
                                   }
                    mqtt_response = automation_utils.send_mqtt_message('device_commands', status_body)
                case ScheduleTypes.WATER_LAWN:
                    # TODO: push back schedule if it has rained since last watering?
                    last_water_end, is_raining = automation_utils.get_last_watering_and_rain_status()

                    if is_raining:
                        # TODO: set schedule's next_execution time
                        continue

                    # TODO: figure this out
                    water_body = {
                                    'device_id': device_id,
                                    'message': 'water',
                                    'message_body': {
                                        'watering_length_minutes': device.watering_length_minutes,
                                        'watering_wait_minutes': device.watering_wait_minutes
                                        'watering_repetitions': device.watering_repetitions,
                                    }
                                  }


                case _:
                    print(f"Unhandled schedule type {active_schedule.schedule_type}")