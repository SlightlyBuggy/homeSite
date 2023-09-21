import util.automation_utils as util
import sprinkler.mqtt as mqtt
from sprinkler.models import IOTDeviceSchedule, IOTDevice
from datetime import datetime, timezone


def handle_status_command(schedule: IOTDeviceSchedule, device: IOTDevice):
    """
    Handle a device status command.  Update the schedule's next_execution property and create a
    IOTDeviceScheduleExecution object

    :param schedule: IOTDeviceSchedule
    :param device: IOTDevice
    :return:
    """

    current_dt = datetime.now(timezone.utc)
    if not schedule.interval_minutes:
        print("Unable to process schedule.  Missing interval_minutes")
        return

    status_body = {
        'device_id': device.device_id,
        'command': mqtt.COMMAND_STATUS
    }

    mqtt_response = mqtt.send_mqtt_message(mqtt.COMMAND_TOPIC, status_body)

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

    current_dt = datetime.now(timezone.utc)
    # get the end time and status of watering event (rain, sprinkler, etc
    last_water_end, watering_in_progress = util.get_last_watering_and_status(device_id=device.device_id)

    # if a watering event is in progress, recalculate the next_execution starting now
    if watering_in_progress:
        schedule.next_execution = util.get_next_schd_using_start_time(schedule=schedule, starting_at=current_dt,
                                                                      interval_minutes=
                                                                      device.minimum_water_interval_hours*60)
        schedule.save()
        return

    # if we have a past water event, calc the next needed watering based on the end of that event
    if last_water_end:
        schedule.next_execution = util.get_next_schd_using_start_time(schedule=schedule, starting_at=last_water_end,
                                                                      interval_minutes=
                                                                      device.minimum_water_interval_hours*60)
        schedule.save()
        return

    # if we've gotten here, we need to command the device to start watering
    water_body = {
        'device_id': device.device_id,
        'command': mqtt.COMMAND_SPRINKLE_START,
        'message_body': {
            'watering_length_minutes': device.watering_length_minutes,
            'watering_wait_minutes': device.watering_wait_minutes,
            'watering_repetitions': device.watering_repetitions,
        }
    }

    mqtt_response = mqtt.send_mqtt_message(mqtt.COMMAND_TOPIC, water_body)

    # push water schedule ahead by one day to allow sprinkling to occur.  if sprinkling happens,
    # the logic above will push out the schedule.  if does not, it will be retried on that day
    # this allows things like manual filling of barrels or water transfer to work
    schedule.next_execution = util.get_next_schd_using_start_time(schedule=schedule, starting_at=current_dt,
                                                                  interval_minutes=
                                                                  device.minimum_water_interval_hours*60)
    schedule.save()

    # create and save the schedule_execution object
    schedule_execution = util.build_schedule_execution(schedule, current_dt, mqtt_response)
    schedule_execution.save()

    # create and save the sprinkler log object
    # TODO: do this in response to a message from the device?
    # TODO: fix inputs
    sprinkle_log = util.build_sprinkle_log(device=device, start_time=current_dt, end_time=current_dt,
                                           water_qty_at_start_gallons=0, water_qty_at_end_gallons=0)
    sprinkle_log.save()

    return
