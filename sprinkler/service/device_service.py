from sprinkler.models import IOTDevice
from datetime import datetime, timezone


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
