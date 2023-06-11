import datetime
import json
from django.http import JsonResponse
from .mqtt import client as mqtt_client
from .models import IOTDevice, IOTDeviceSchedule, IOTDeviceScheduleExecution, ScheduleTypes

import util.automation_utils as util


def publish_message(request):
    # TODO: validate request body
    request_data = json.loads(request.body)

    mqtt_response = util.send_mqtt_message(request_data['topic'], request_data['body'])
    return mqtt_response


def test_device_message(request):

    mqtt_response = util.send_mqtt_message(util.REPORT_TOPIC, 'test device message sent')
    return mqtt_response


def test_device_command(request):

    mqtt_response = util.send_mqtt_message(util.COMMAND_TOPIC, 'test device command sent')
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
                    handle_status_command(schedule=active_schedule, device=device)

                case ScheduleTypes.SPRINKLE:
                    handle_sprinkle_command(schedule=active_schedule, device=device)

                case _:
                    print(f"Unhandled schedule type {active_schedule.schedule_type}")


def handle_status_command(schedule: IOTDeviceSchedule, device: IOTDevice):
    """
    Handle a device status command.  Update the schedule's next_execution property and create a
    IOTDeviceScheduleExecution object

    :param schedule: IOTDeviceSchedule
    :param device: IOTDevice
    :return:
    """

    current_dt = datetime.datetime.now()
    if not schedule.interval_minutes:
        print("Unable to process schedule.  Missing interval_minutes")
        return

    status_body = {
        'device_id': device.id,
        'message': util.COMMAND_STATUS,
        'message_body': None
    }

    mqtt_response = util.send_mqtt_message('device_commands', status_body)

    # set the next scheduled time
    schedule.next_execution = util.get_next_schd_using_interval(schedule)
    schedule.save()

    # create and save the schedule_execution object
    schedule_execution = util.build_schedule_execution(schedule, current_dt, mqtt_response)
    schedule_execution.save()
    return


def handle_sprinkle_command(schedule: IOTDeviceSchedule, device: IOTDevice):
    """
    Handle a spinkle lawn command.  Update the schedule's next_execution property based on existing sprinkle/water
    events, and send a sprinkle command if needed. Create a IOTDeviceScheduleExecution object

    :param schedule: IOTDeviceSchedule
    :param device: IOTDevice
    :return:
    """

    current_dt = datetime.datetime.now()
    # get the end time and status of watering event (rain, sprinkler, etc
    last_water_end, watering_in_progress = util.get_last_watering_and_status(device_id=device.id)

    # if a watering event is in progress, recalculate the next_execution starting now
    if watering_in_progress:
        schedule.next_execution = util.get_next_schd_using_start_time(schedule=schedule, starting_at=current_dt)
        schedule.save()
        return

    # if we have a past water event, calc the next needed watering based on the end of that event
    if last_water_end:
        schedule.next_execution = util.get_next_schd_using_start_time(schedule=schedule, starting_at=last_water_end)
        schedule.save()
        return

    # if we've gotten here, we need to command the device to start watering
    water_body = {
        'device_id': device.id,
        'message': util.COMMAND_SPRINKLE,
        'message_body': {
            'watering_length_minutes': device.watering_length_minutes,
            'watering_wait_minutes': device.watering_wait_minutes,
            'watering_repetitions': device.watering_repetitions,
        }
    }

    mqtt_response = util.send_mqtt_message(util.COMMAND_TOPIC, water_body)

    # push water schedule ahead by one day to allow sprinkling to occur.  if sprinkling happens,
    # the logic above will push out the schedule.  if does not, it will be retried on that day
    # this allows things like manual filling of barrels or water transfer to work
    schedule.next_execution = util.get_next_schd_using_start_time(schedule=schedule, starting_at=current_dt,
                                                                  interval_minutes=util.MINUTES_IN_DAY)
    schedule.save()

    # create and save the schedule_execution object
    schedule_execution = util.build_schedule_execution(schedule, current_dt, mqtt_response)
    schedule_execution.save()
    return
