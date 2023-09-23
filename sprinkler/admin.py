from django.contrib import admin

from .models import IOTDevice, IOTDeviceSchedule, IOTDeviceScheduleExecution, RainLog, DeviceStatusLog, \
    Setting, SprinklerLog

admin.site.register(IOTDevice)
admin.site.register(IOTDeviceSchedule)
admin.site.register(IOTDeviceScheduleExecution)
admin.site.register(RainLog)
admin.site.register(SprinklerLog)
admin.site.register(DeviceStatusLog)
admin.site.register(Setting)


class RainLogAdmin(admin.ModelAdmin):

    list_display = 'start_time'


class IOTDeviceAdmin(admin.ModelAdmin):

    list_display = 'device_id'

