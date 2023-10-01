from django.db import models
from datetime import datetime, timezone


# base class that handles created/edited fields
class BaseModel(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    class Meta:
        abstract = True


# device.  Prototype is planned to have a water level sensor and watering pump
class Device(BaseModel):

    name = models.CharField(max_length=200)

    # peripheral devices.  only water level sensor and pump are planned initially, but later models could add things
    # like a flow sensor, rain sensor, etc
    has_water_level_pressure_sensor = models.BooleanField(default=False)
    has_watering_pump = models.BooleanField(default=False)

    # water storage configuration
    num_barrels = models.IntegerField(null=True)
    barrel_cross_sectional_area_in2 = models.FloatField(null=True)

    # watering configuration
    # minimum time to wait between water events before trying to water
    minimum_water_interval_hours = models.IntegerField()

    # watering config
    # to allow the soil to absorb water, the sprinkler will run for watering_length_minutes, then wait for
    # watering_wait_minutes, and do that watering_repetitions times

    # when watering, this is how long the sprinklers will run
    watering_length_minutes = models.IntegerField()

    # the system will wait this long until running the sprinkler again
    watering_wait_minutes = models.IntegerField()

    # the cycle will repeat this many times
    watering_repetitions = models.IntegerField()

    # based on pin strapping
    device_id = models.IntegerField()

    # calibration for the supply voltage reading
    cal_low_ticks_voltage = models.IntegerField(null=True)
    cal_low_voltage = models.FloatField(null=True)

    cal_high_ticks_voltage = models.FloatField(null=True)
    cal_high_voltage = models.FloatField(null=True)

    # calibration for water pressure
    cal_low_pressure_psi = models.FloatField(null=True)
    cal_high_pressure_psi = models.FloatField(null=True)

    # sleep/awake time
    time_awake_start_hour_utc = models.IntegerField(null=True)
    time_awake_stop_hour_utc = models.IntegerField(null=True)

    class Meta:
        abstract = True


# include properties specific to a connected device.  All devices should be connected, but this is a nice abstraction
class IOTDevice(Device):

    def __str__(self):
        return f"{self.device_id} - {self.name}"

    ipv4_address = models.CharField(max_length=15)
    port = models.IntegerField()

    def get_latest_status(self):
        try:
            return self.devicestatuslog_set.all().order_by('-created')[0]
        except IndexError:
            pass

    # TODO: need to do a more robust check for offline/offline
    def should_be_awake(self):
        if self.time_awake_start_hour_utc == self.time_awake_stop_hour_utc:
            return True

        dt_awake_start = datetime.now(timezone.utc).replace(hour=self.time_awake_start_hour_utc, minute=0, second=0,
                                                            microsecond=0)
        dt_awake_end = datetime.now(timezone.utc).replace(hour=self.time_awake_stop_hour_utc, minute=0, second=0,
                                                          microsecond=0)

        current_dt = datetime.now(timezone.utc)

        if dt_awake_start < current_dt < dt_awake_end:
            return True

        return False


# types of schedules
class ScheduleTypes(models.TextChoices):
    SPRINKLE = 'sprinkle'
    GET_DEVICE_STATUS = 'get_status'


# Device-specific schedule configuration
class IOTDeviceSchedule(BaseModel):

    device = models.ForeignKey(IOTDevice, on_delete=models.CASCADE, related_name='schedules')

    schedule_type = models.CharField(max_length=100, choices=ScheduleTypes.choices,
                                     default=ScheduleTypes.GET_DEVICE_STATUS)
    # If only hour is populated, this means every day on that hour.  if only minute, every hour on that
    # minute.  Only one of the two should be populated
    hour = models.IntegerField()
    minute = models.IntegerField()

    # if this is populated, schedule initially starts at above value then repeats every interval_minutes
    interval_minutes = models.IntegerField()

    # this will be managed by the automation
    next_execution = models.DateTimeField(auto_now=False)

    # whether to consider this schedule
    active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.device} - {self.schedule_type}"


# log of scheduled actions
class IOTDeviceScheduleExecution(BaseModel):

    iot_device_schedule = models.ForeignKey(IOTDeviceSchedule, on_delete=models.CASCADE)

    schedule_type = models.CharField(max_length=100, choices=ScheduleTypes.choices,
                                     default=ScheduleTypes.GET_DEVICE_STATUS)

    start_time = models.DateTimeField(auto_now=False)
    exit_code = models.IntegerField()

    def __str__(self):

        return "{device_id} - {device_name} | {schedule_type} | {exec_time}".format(
            device_id=self.iot_device_schedule.device.device_id,
            device_name=self.iot_device_schedule.device.name,
            schedule_type=self.schedule_type,
            exec_time=self.start_time)


# rain log
class RainLog(BaseModel):

    start_time = models.DateTimeField(auto_now=False, null=True)
    end_time = models.DateTimeField(auto_now=False, null=True)
    total_amount_inches = models.FloatField(null=True)

    def __str__(self):
        
        if self.end_time and self.start_time:
            return "{start} - {end}; Total: {total:.2f} inches".format(
                start=self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                end=self.end_time.strftime('%Y-%m-%d %H:%M:%S'),
                total=self.total_amount_inches)

        if self.start_time:
            return f"{self.start_time} - ongoing"

        return "No start time"


# wanted to call this WaterLog (ha) but that was too confusing
class SprinklerLog(BaseModel):
    device = models.ForeignKey(IOTDevice, on_delete=models.CASCADE)

    start_time = models.DateTimeField(auto_now=False)
    end_time = models.DateTimeField(auto_now=False)
    water_qty_at_start_gallons = models.FloatField()
    water_level_at_end_gallons = models.FloatField()

    def __str__(self):
        return f"{self.device.name} - {self.created.strftime('%Y-%m-%d %H:%M:%S')}"


# device status
class DeviceStatusLog(BaseModel):
    device = models.ForeignKey(IOTDevice, on_delete=models.CASCADE)
    supply_voltage_ticks = models.IntegerField(null=True)
    supply_voltage = models.FloatField(null=True)
    water_pressure_psi = models.FloatField(null=True)

    def __str__(self):
        return f"{self.device.name} - {self.created.strftime('%Y-%m-%d %H:%M:%S')} | {self.supply_voltage} V | " \
               f"{self.water_pressure_psi} PSI"


# store global settings - not sure what exactly, but it might be useful
class Setting(BaseModel):
    key = models.TextField()
    value = models.TextField()
