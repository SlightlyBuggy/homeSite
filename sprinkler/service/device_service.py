from sprinkler.models import ServerToDeviceCommand
from datetime import datetime, timezone
from sprinkler.service.schedule_service import execute_scheduled_tasks
from util.automation_utils import get_voltage_from_ticks_and_cal
from sprinkler.models import DeviceStatusLog, IOTDevice
import sprinkler.constants as sprinkler_constants


def should_device_be_awake(device: IOTDevice):
    """
    Return true if the device should be awake
    :param device: IOTDevice
    :return: boolean
    """
    hour_awake_start = device.time_awake_start_hour_utc
    hour_awake_end = device.time_awake_stop_hour_utc

    if hour_awake_end == hour_awake_end:
        return True

    dt_awake_start = datetime.now(timezone.utc).replace(hour=hour_awake_start, minute=0, second=0, microsecond=0)
    dt_awake_end = datetime.now(timezone.utc).replace(hour=hour_awake_end, minute=0, second=0, microsecond=0)

    current_dt = datetime.now(timezone.utc)

    return dt_awake_start < current_dt < dt_awake_end


def handle_device_status(device_id, status, message_sender) -> None:
    """
    Take appropriate action when a device reports its status

    :param device_id: IOTDevice
    :param status: status object from device
    :param message_sender:
    :return:
    """
    voltage_ticks = None
    voltage = None

    if 'voltage_ticks' in status:
        voltage_ticks = status['voltage_ticks']
        devices_with_device_id: list[IOTDevice] = IOTDevice.objects.filter(device_id=device_id)[:1]

        if devices_with_device_id:
            this_device: IOTDevice = devices_with_device_id[0]
            voltage = get_voltage_from_ticks_and_cal(input_ticks=voltage_ticks,
                                                     cal_low_ticks=this_device.cal_low_ticks_voltage,
                                                     cal_low_voltage=this_device.cal_low_voltage,
                                                     cal_high_ticks=this_device.cal_high_ticks_voltage,
                                                     cal_high_voltage=this_device.cal_high_voltage)

    # handle water pressure
    water_pressure_ticks = None
    if 'pressure_ticks' in status:
        water_pressure_ticks = status['pressure_ticks']

    transmitting_device = IOTDevice.objects.get(device_id=device_id)

    if not transmitting_device:
        print(f"Unable to handle device status message.  unknown device id {device_id}")
        return

    new_device_status = DeviceStatusLog(device=transmitting_device, supply_voltage=voltage,
                                        supply_voltage_ticks=voltage_ticks,
                                        water_pressure_ticks=water_pressure_ticks)
    new_device_status.save()

    # TODO: this is a hack until the device can tell us whether it can sprinkle
    can_sprinkle = device_measured_enough_water_to_sprinkle_from_last_status(transmitting_device)

    # attempt to execute any tasks we need to.  if we did, we're done.
    tasks_executed = execute_scheduled_tasks(device=transmitting_device, can_sprinkle=can_sprinkle)
    if tasks_executed:
        return

    # if the device should be awake now, don't tell it to do anything
    device_should_be_awake = transmitting_device.should_be_awake_now()
    if device_should_be_awake:
        print(f"Telling device {device_id} to stay awake")
        return

    # if the device needs to be awake later today, put it to sleep for now
    if transmitting_device.should_be_awake_later_today():
        payload = {
            'device_id': device_id,
            'command': ServerToDeviceCommand.SLEEP.value,
            'body': {
                'sleep_length_minutes': "60" # TODO: scale this so it wakes up right after the scheduled task
            }
        }

        return message_sender(sprinkler_constants.COMMAND_TOPIC, str(payload))

    # if we've made it here, the device doesn't have any tasks to accomplish now, doesn't need to be awake now,
    # doesn't need to be awake later, and has no tasks later.  It should be shut off for the day
    print(f"Telling device {device_id} to turn off")
    payload = {
        'device_id': device_id,
        'command': ServerToDeviceCommand.POWER_OFF.value,
    }

    message_sender(sprinkler_constants.COMMAND_TOPIC, str(payload))

    return


def device_measured_enough_water_to_sprinkle_from_last_status(device: IOTDevice) -> bool:
    """
    Based on last status, does the device have enough water to sprinkle?
    :param device: IOTDevice
    :return: bool - whether the device reported enough water to sprinkle or not
    """

    if not device.cal_low_pressure_ticks or not device.cal_high_pressure_ticks:
        return False

    last_status_qs = DeviceStatusLog.objects.filter(device=device).order_by('-created')[:1]
    if not last_status_qs:
        return False

    last_status: DeviceStatusLog = last_status_qs[0]

    last_measured_ticks = last_status.water_pressure_ticks
    if not last_measured_ticks:
        return False

    min_percent = sprinkler_constants.MIN_PERCENT_TO_WATER

    # interpolate to determine min ticks based on min percent
    min_ticks = (device.cal_high_pressure_ticks -
                 device.cal_low_pressure_ticks)*min_percent/100 + device.cal_low_pressure_ticks

    return last_measured_ticks >= min_ticks


