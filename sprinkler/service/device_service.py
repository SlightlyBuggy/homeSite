from sprinkler.models import ServerToDeviceCommand
from sprinkler.service.schedule_service import execute_scheduled_tasks
from sprinkler.models import DeviceStatusLog, IOTDevice
import sprinkler.constants as sprinkler_constants
from sprinkler.classes.ParsedDeviceStatus import DeviceStatus
from sprinkler.service.command_service import send_command


def handle_device_status(device_id, status) -> None:

    transmitting_device = get_device_by_device_id(device_id)
    device_status: DeviceStatus = DeviceStatus(device_id, status)

    if not transmitting_device:
        print(f"Unable to handle device status message.  unknown device id {device_id}")
        return

    build_and_save_device_status_log(transmitting_device, device_status)

    respond_to_device(transmitting_device)


def device_measured_enough_water_to_sprinkle_from_last_status(device: IOTDevice) -> bool:

    if not pressure_cal_configured(device):
        return False

    last_measured_ticks = get_measured_ticks_from_last_status_log(device)

    if not last_measured_ticks:
        return False

    minimum_measured_ticks = get_minimum_measured_ticks(device)

    return last_measured_ticks >= minimum_measured_ticks


def pressure_cal_configured(device: IOTDevice) -> bool:

    if not device.cal_low_pressure_ticks or not device.cal_high_pressure_ticks:
        return False

    return True


def get_measured_ticks_from_last_status_log(device: IOTDevice) -> None | int:

    last_status_log = DeviceStatusLog.objects.filter(device=device).order_by('-created')[:1]
    if not last_status_log:
        return None

    last_status: DeviceStatusLog = last_status_log[0]

    last_measured_ticks = last_status.water_pressure_ticks
    if not last_measured_ticks:
        return None

    return last_measured_ticks


def get_minimum_measured_ticks(device: IOTDevice):
    min_ticks = (device.cal_high_pressure_ticks -
                 device.cal_low_pressure_ticks) * sprinkler_constants.MIN_PERCENT_TO_WATER / 100 + \
                device.cal_low_pressure_ticks

    return min_ticks


def get_device_by_device_id(device_id: int) -> IOTDevice | None:
    device: IOTDevice | None = IOTDevice.objects.filter(device_id=device_id).first()

    return device


def build_and_save_device_status_log(device: IOTDevice, status: DeviceStatus):

    new_device_status = DeviceStatusLog(device=device, supply_voltage=status.voltage,
                                        supply_voltage_ticks=status.voltage_ticks,
                                        water_pressure_ticks=status.water_pressure_ticks)
    new_device_status.save()


def respond_to_device(device: IOTDevice):
    can_sprinkle = device_measured_enough_water_to_sprinkle_from_last_status(device)

    # if any tasks are communicated, we need to wait for the device to carry out the commands.  then it will report
    # status again
    tasks_communicated = execute_scheduled_tasks(device=device, can_sprinkle=can_sprinkle)
    if tasks_communicated:
        return

    device_should_be_awake = device.should_be_awake_now()
    if device_should_be_awake:
        tell_device_to_stay_awake(device)
        return

    if device.should_be_awake_later_today() and can_sprinkle:
        tell_device_to_sleep_for_one_hour(device)
        return

    tell_device_to_power_off(device)


def tell_device_to_sleep_for_one_hour(device: IOTDevice):

    command_body = { 'sleep_length_minutes': "60" }

    send_command(device, ServerToDeviceCommand.SLEEP.value, command_body=command_body)


def tell_device_to_power_off(device: IOTDevice):
    print(f"Telling device {device.device_id} to turn off")

    command_body = {'sleep_length_minutes': "60"}

    send_command(device, ServerToDeviceCommand.POWER_OFF.value, command_body=command_body)


def tell_device_to_stay_awake(device: IOTDevice):

    print("Not actually doing anything because a 'stay_awake' command has not been implemented")
