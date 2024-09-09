from sprinkler.models import IOTDevice
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

    pending_schedules, future_schedules_today = transmitting_device.today_active_schedules()

    # if we've got pending things to do, do them
    if pending_schedules:
        execute_scheduled_tasks(device=transmitting_device)
        return

    # if the device should be awake now, don't tell it to do anything
    device_should_be_awake = transmitting_device.should_be_awake_now()
    if device_should_be_awake:
        print(f"Telling device {device_id} to stay awake")
        return

    # if the device needs to be awake later today, or has things to do later today, put it to sleep
    if future_schedules_today:
        payload = {
            'device_id': device_id,
            'command': sprinkler_constants.COMMAND_SLEEP,
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
        'command': sprinkler_constants.COMMAND_POWER_OFF,
    }

    message_sender(sprinkler_constants.COMMAND_TOPIC, str(payload))

    return
