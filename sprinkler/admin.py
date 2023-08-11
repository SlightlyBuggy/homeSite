from django.contrib import admin

from .models import IOTDevice, IOTDeviceSchedule, IOTDeviceScheduleExecution, RainLog, DeviceStatusLog, \
    Setting

admin.site.register(IOTDevice)
admin.site.register(IOTDeviceSchedule)
admin.site.register(IOTDeviceScheduleExecution)
admin.site.register(RainLog)
admin.site.register(DeviceStatusLog)
admin.site.register(Setting)
