from django.db import models


# base class that handles created/edited fields
class BaseModel(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# device.  Prototype is planned to have a water level sensor and watering pump
class Device(BaseModel):

    name = models.CharField(max_length=200)

    # peripheral devices.  only water level sensor and pump are planned initially, but later models could add things
    # like a flow sensor, rain sensor, etc
    has_water_level_pressure_sensor = models.BooleanField(default=False)
    has_watering_pump = models.BooleanField(default=False)

    # conversion from reported sensor value to inches water
    # rather than trying to fill each barrel and calibrating, we can use a value based on the docs and test later
    # when the barrel is naturally filled up.  This assumes a constant cross-section barrel, which seems reasonable
    sensor_val_to_inches_water_multiplier = models.FloatField()

    # it should just read zero, but this is just in case
    sensor_reading_at_zero = models.FloatField(default=0.0)

    # water storage configuration
    num_barrels = models.IntegerField(max_length=2)
    barrel_cross_sectional_area_in2 = models.FloatField()

    # watering configuration
    # minimum time to wait between water events before trying to water
    minimum_water_interval_hours = models.IntegerField(max_length=3)

    # watering config
    # to allow the soil to absorb water, the sprinkler will run for watering_length_minutes, then wait for
    # watering_wait_minutes, and do that watering_repetitions times

    # when watering, this is how long the sprinklers will run
    watering_length_minutes = models.IntegerField(max_length=2)

    # the system will wait this long until running the sprinkler again
    watering_wait_minutes = models.IntegerField(max_length=2)

    # the cycle will repeat this many times
    watering_repetitions = models.IntegerField(max_length=1)

    class Meta:
        abstract = True


# include properties specific to a connected device.  All devices should be connected, but this is a nice abstraction
class IOTDevice(Device):

    ipv4_address = models.CharField(max_length=15)
    port = models.IntegerField(max_length=5)


# types of schedules
class ScheduleTypes(models.TextChoices):
    WATER_LAWN = 'water_lawn'
    GET_DEVICE_STATUS = 'get_status'


# Device-specific schedule configuration
class IOTDeviceSchedule(BaseModel):

    device = models.ForeignKey(IOTDevice, on_delete=models.CASCADE)

    schedule_type = models.CharField(max_length=2, choices=ScheduleTypes.choices,
                                     default=ScheduleTypes.GET_DEVICE_STATUS)
    # If only day_of_week is populated, this means that day
    # at midnight.  If only hour is populated, this means every day on that hour.  if only minute, every hour on that
    # minute.  If more values are populated, then the schedule is filtered accordingly
    day_of_week = models.IntegerField(max_length=1)
    hour = models.IntegerField(max_length=2)
    minute = models.IntegerField(max_length=2)

    # if this is populated, schedule initially starts at above value then repeats every interval_minutes
    interval_minutes = models.IntegerField(max_length=4)

    # this will be managed by the automation
    next_execution = models.DateTimeField()


# log of scheduled actions
class IOTDeviceScheduleExecution(BaseModel):

    iot_device_schedule = models.ForeignKey(IOTDeviceSchedule, on_delete=models.CASCADE)

    schedule_type = models.CharField(max_length=2, choices=ScheduleTypes.choices,
                                     default=ScheduleTypes.GET_DEVICE_STATUS)

    start_time: models.DateTimeField()
    end_time: models.DateTimeField()
    exit_code = models.IntegerField(max_length=2)
    messages = models.JSONField()


# rain log
class RainModel(BaseModel):

    start_time: models.DateTimeField()
    end_time: models.DateTimeField()
    total_amount_inches = models.FloatField()


# water log (ha)
class WaterLog(BaseModel):
    device = models.ForeignKey(IOTDevice, on_delete=models.CASCADE)

    start_time: models.DateTimeField()
    end_time: models.DateTimeField()
    water_qty_at_start_gallons = models.FloatField()
    water_level_at_end_gallons = models.FloatField()


# device status
class DeviceStatusLog(BaseModel):
    device = models.ForeignKey(IOTDevice, on_delete=models.CASCADE)

    supply_voltage = models.FloatField()
    water_level_inches = models.FloatField()