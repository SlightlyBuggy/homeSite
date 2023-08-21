from django.shortcuts import render
from .models import IOTDevice


def device_status(request):

    all_devices = IOTDevice.objects.all()

    context = {'all_devices': all_devices}

    # for device in all_devices:
    #     reordered_statuses = device.devicestatuslog_set.order_by('created')
    #     device.devicestatuslog_set.set(reordered_statuses)

    return render(request, 'sprinkler/device_status.html', context)

