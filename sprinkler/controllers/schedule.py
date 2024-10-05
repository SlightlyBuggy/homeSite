from sprinkler.models import IOTDevice
from sprinkler.service import command_service


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
