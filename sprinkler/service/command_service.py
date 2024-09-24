import util.automation_utils as util
import sprinkler.mqtt as mqtt
from sprinkler.models import IOTDeviceSchedule, IOTDevice
from datetime import datetime, timezone
from django.views.decorators.csrf import csrf_exempt
from sprinkler import constants


@csrf_exempt
def handle_status_command(device: IOTDevice):
    """
    Handle a device status command.  Update the schedule's next_execution property and create a
    IOTDeviceScheduleExecution object

    :param device: IOTDevice
    :return:
    """

    status_body = {
        'device_id': device.device_id,
        'command': constants.COMMAND_STATUS
    }

    mqtt_response = mqtt.send_mqtt_message(constants.COMMAND_TOPIC, status_body)
    return


# TODO: get rid of can_sprinkle from this and other functions once the device can tell us whether it can sprinkle
@csrf_exempt
def handle_sprinkle_command(schedule: IOTDeviceSchedule, device: IOTDevice, can_sprinkle) -> bool:
    """
    Handle a spinkle lawn command.  Update the schedule's next_execution property.
    Create a IOTDeviceScheduleExecution object.

    :param schedule: IOTDeviceSchedule
    :param device: IOTDevice
    :param can_sprinkle: boolean - indicates whether device has enough water to sprinkle
    :return:
    """

    # TODO: this is a hack until the device can tell us whether it can sprinkle or not
    if not can_sprinkle:
        return False

    current_dt = datetime.now(timezone.utc)

    # if we've gotten here, we need to command the device to start watering
    water_body = {
        'device_id': device.device_id,
        'command': constants.COMMAND_SPRINKLE_START,
        'body': {
            'watering_length_minutes': str(device.watering_length_minutes),
            'watering_wait_minutes': str(device.watering_wait_minutes),
            'watering_repetitions': str(device.watering_repetitions),
        }
    }

    mqtt_response = mqtt.send_mqtt_message(constants.COMMAND_TOPIC, water_body)

    # update the schedule
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

    return True
