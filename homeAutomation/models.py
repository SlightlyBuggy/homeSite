from django.db import models


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

    # conversion from reported sensor value to inches water
    # rather than trying to fill each barrel and calibrating, we can use a value based on the docs and test later
    # when the barrel is naturally filled up.  This assumes a constant cross-section barrel, which seems reasonable
    sensor_val_to_inches_water_multiplier = models.FloatField()

    # it should just read zero, but this is just in case
    sensor_reading_at_zero = models.FloatField(default=0.0)

    # water storage configuration
    num_barrels = models.IntegerField()
    barrel_cross_sectional_area_in2 = models.FloatField()

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
    # TODO: implement pin strapping in Arduino code
    device_id = models.IntegerField()

    class Meta:
        abstract = True


# include properties specific to a connected device.  All devices should be connected, but this is a nice abstraction
class IOTDevice(Device):

    ipv4_address = models.CharField(max_length=15)
    port = models.IntegerField()


# types of schedules
class ScheduleTypes(models.TextChoices):
    SPRINKLE = 'sprinkle'
    GET_DEVICE_STATUS = 'get_status'


# Device-specific schedule configuration
class IOTDeviceSchedule(BaseModel):

    device_id = models.ForeignKey(IOTDevice, on_delete=models.CASCADE, related_name='schedules')

    schedule_type = models.CharField(max_length=100, choices=ScheduleTypes.choices,
                                     default=ScheduleTypes.GET_DEVICE_STATUS)
    # If only hour is populated, this means every day on that hour.  if only minute, every hour on that
    # minute.  Only one of the two should be populated
    hour = models.IntegerField()
    minute = models.IntegerField()

    # if this is populated, schedule initially starts at above value then repeats every interval_minutes
    interval_minutes = models.IntegerField()

    # this will be managed by the automation
    next_execution = models.DateTimeField()

    # whether to consider this schedule
    active = models.BooleanField(default=False)


# log of scheduled actions
class IOTDeviceScheduleExecution(BaseModel):

    iot_device_schedule_id = models.ForeignKey(IOTDeviceSchedule, on_delete=models.CASCADE)

    schedule_type = models.CharField(max_length=100, choices=ScheduleTypes.choices,
                                     default=ScheduleTypes.GET_DEVICE_STATUS)

    start_time: models.DateTimeField()
    exit_code = models.IntegerField()


# rain log
class RainLog(BaseModel):

    start_time: models.DateTimeField()
    end_time: models.DateTimeField()
    total_amount_inches = models.FloatField()


# wanted to call this WaterLog (ha) but that was too confusing
class SprinklerLog(BaseModel):
    device_id = models.ForeignKey(IOTDevice, on_delete=models.CASCADE)

    start_time: models.DateTimeField()
    end_time: models.DateTimeField()
    water_qty_at_start_gallons = models.FloatField()
    water_level_at_end_gallons = models.FloatField()


# device status
class DeviceStatusLog(BaseModel):
    device_id = models.ForeignKey(IOTDevice, on_delete=models.CASCADE)

    supply_voltage = models.FloatField()
    water_level_inches = models.FloatField()


# store global settings - not sure what exactly, but it might be useful
class Setting(BaseModel):
    key = models.TextField()
    value = models.TextField()
