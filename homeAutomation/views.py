import datetime
import json
from django.http import JsonResponse
from .mqtt import client as mqtt_client
from .models import IOTDevice, IOTDeviceSchedule, IOTDeviceScheduleExecution, ScheduleTypes
from util.automation_utils import send_mqtt_message, get_last_watering_and_status, COMMAND_TOPIC, MINUTES_IN_DAY, \
    MESSAGE_TOPIC, get_next_scheduled_daily_time


def publish_message(request):
    # TODO: validate request body
    request_data = json.loads(request.body)

    mqtt_response = send_mqtt_message(request_data['topic'], request_data['body'])
    return mqtt_response


def test_device_message(request):

    mqtt_response = send_mqtt_message(MESSAGE_TOPIC, 'test device message sent')
    return mqtt_response


def test_device_command(request):

    mqtt_response = send_mqtt_message(COMMAND_TOPIC, 'test device command sent')
    return mqtt_response


def execute_scheduled_tasks(request):

    # grab active schedules
    active_schedules: list[IOTDeviceSchedule] = IOTDeviceSchedule.objects.filter(active=True)
    current_dt = datetime.datetime.now()

    for active_schedule in active_schedules:

        # check if schedule should be executed now
        if active_schedule.next_execution <= current_dt:

            device: IOTDevice = IOTDevice.objects.get(pk=active_schedule.device_id)
            device_id = device.id

            match active_schedule.schedule_type:
                case ScheduleTypes.GET_DEVICE_STATUS:

                    status_body = {
                                    'device_id': device_id,
                                    'message': 'status',
                                    'message_body': None
                                   }
                    mqtt_response = send_mqtt_message('device_commands', status_body)
                    # TODO: what to do with mqtt_response?

                case ScheduleTypes.WATER_LAWN:
                    # TODO: push back schedule if it has rained since last watering?
                    last_water_end, watering_in_progress = get_last_watering_and_status(
                        device_id=device_id)

                    if watering_in_progress:
                        # since a water event is in progress, push the next_execution back by interval_minutes from now
                        active_schedule.next_execution = get_next_scheduled_daily_time(schedule=active_schedule,
                                                                                       starting_at=current_dt)
                        active_schedule.save()
                        continue

                    # if we have a past water event, calc the next needed watering based on the schedule, and push back
                    # the schedule if that time is in the future.  This accounts for rain and manually-triggered
                    # watering events
                    if last_water_end:
                        next_required_sprinkling = get_next_scheduled_daily_time(schedule=active_schedule,
                                                                                 starting_at=last_water_end)

                        if next_required_sprinkling > current_dt:
                            active_schedule.next_execution = next_required_sprinkling
                            active_schedule.save()
                            continue

                    # if we've gotten here, we need to command the device to start watering
                    water_body = {
                                    'device_id': device_id,
                                    'message': 'water',
                                    'message_body': {
                                        'watering_length_minutes': device.watering_length_minutes,
                                        'watering_wait_minutes': device.watering_wait_minutes,
                                        'watering_repetitions': device.watering_repetitions,
                                    }
                                  }
                    mqtt_response = send_mqtt_message(COMMAND_TOPIC, water_body)

                    # push water schedule ahead by one day to allow sprinkling to occur.  if sprinkling happens,
                    # the logic above will push out the schedule.  if it is not, it will be retried on that day
                    # this allows things like manual filling of barrels or water transfer to work
                    active_schedule.next_execution = get_next_scheduled_daily_time(schedule=active_schedule,
                                                                                   starting_at=current_dt,
                                                                                   interval_minutes=MINUTES_IN_DAY)


                case _:
                    print(f"Unhandled schedule type {active_schedule.schedule_type}")