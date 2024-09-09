from sprinkler.models import IOTDevice
from sprinkler.service import command_service


# TODO: break this into separate things.  there should be two funtions: that one pings all known devices for status,
# and the other that updates schedules.  The former will catch any devices that are online and waiting
def ping_devices_for_status(request):
    """
    This endpoint asks each device to report status

    :param request:
    :return: None
    """

    devices: list[IOTDevice] = IOTDevice.objects.all()

    for device in devices:
        command_service.handle_status_command(device=device)

    return
