import util.automation_utils as util
import sprinkler.service.mqtt_service as mqtt
from sprinkler.models import IOTDeviceSchedule, IOTDevice, ServerToDeviceCommand, ServerToDeviceCommandLog
from datetime import datetime, timezone
from django.views.decorators.csrf import csrf_exempt
from sprinkler import constants


@csrf_exempt
def handle_status_command(device: IOTDevice):
    """
    Handle a device status command.

    :param device: IOTDevice
    :return:
    """

    mqtt_response = send_command(device=device, command=ServerToDeviceCommand.STATUS.value)
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

    command_body = {
        'watering_length_minutes': str(device.watering_length_minutes),
        'watering_wait_minutes': str(device.watering_wait_minutes),
        'watering_repetitions': str(device.watering_repetitions),
    }

    mqtt_response = send_command(device=device, command=ServerToDeviceCommand.SPRINKLE_START.value,
                                 command_body=command_body)

    # update the schedule
    schedule.next_execution = util.get_next_schd_using_start_time(schedule=schedule, starting_at=current_dt)
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

# TODO: need test coverage of this function
def send_command(device: IOTDevice, command: ServerToDeviceCommand, command_body=None):

    # TODO: allow null in ServerToDeviceCommandLog?
    if command_body is None:
        command_body = {}
    command_log = ServerToDeviceCommandLog(device=device, command=command, body=command_body)
    command_log.save()

    command_dict = command_log.__dict__
    response = mqtt.client.send_mqtt_message(constants.COMMAND_TOPIC, command_dict)
    return response
