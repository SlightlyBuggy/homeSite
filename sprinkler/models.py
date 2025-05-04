import uuid

from django.db import models
from datetime import datetime, timezone
from django.utils import timezone


# base class that handles created/edited fields
class BaseModel(models.Model):

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    objects = models.Manager()

    class Meta:
        abstract = True


# IOT device
class IOTDevice(BaseModel):

    name = models.CharField(max_length=200)

    # peripheral devices.  only water level sensor and pump are planned initially, but later models could add things
    # like a flow sensor, rain sensor, etc
    has_water_level_pressure_sensor = models.BooleanField(default=False)
    has_watering_pump = models.BooleanField(default=False)

    # water storage configuration
    num_barrels = models.IntegerField(null=True)
    barrel_cross_sectional_area_in2 = models.FloatField(null=True)

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
    cal_low_pressure_ticks = models.IntegerField(null=True)
    cal_high_pressure_ticks = models.IntegerField(null=True)

    # override to allow manual control
    stay_awake = models.BooleanField(default=False)

    def get_latest_status(self):
        try:
            return self.devicestatuslog_set.all().order_by('-created')[0]
        except IndexError:
            return None

    def get_latest_command(self):
        try:
            return self.servertodevicecommandlog_set.all().order_by('-created')[0]
        except IndexError:
            return None

    def get_today_active_schedules(self):

        current_dt = datetime.now(timezone.utc)

        # if a device checks in at 7:30 p.m. CDT, that would be 00:30 the next day UTC.  Need to compare in local time
        # so we don't say there's a schedule today when really it's the next day
        local_dt = timezone.localtime(current_dt)
        current_date = local_dt.date()

        these_active_device_schedules = self.iotdeviceschedule_set.all().filter(active=True)

        today_schedules = [sched for sched in these_active_device_schedules if
                           sched.next_execution.date() == current_date]
        pending_schedules = [sched for sched in today_schedules if sched.next_execution <= current_dt]
        future_schedules_today = [sched for sched in today_schedules if sched.next_execution > current_dt]

        return pending_schedules, future_schedules_today

    def should_be_awake_later_today(self):
        pending_schedules, future_schedules = self.get_today_active_schedules()

        if future_schedules:
            return True

        return False

    def get_voltage_from_voltage_ticks(self, voltage_ticks):
        voltage = (voltage_ticks - self.cal_low_ticks_voltage) * (self.cal_high_voltage - self.cal_low_voltage) / (
                self.cal_high_ticks_voltage - self.cal_low_ticks_voltage) + self.cal_low_voltage
        return voltage

    def should_be_awake_now(self):
        """
        Returns True if device should be awake now.  During this period,
        the device should be listening for commands.  This allows manual control.
        :return: Boolean
        """

        # always stay online if that is configured
        if self.stay_awake:
            return True

        return False

    def has_water_calibration(self):
        return self.cal_low_pressure_ticks is not None and self.cal_high_pressure_ticks is not None

    def __str__(self):
        return f"{self.device_id} - {self.name}"


# types of schedules
class ScheduleTypes(models.TextChoices):
    SPRINKLE = 'sprinkle'


class ServerToDeviceCommand(models.TextChoices):
    STATUS = 'status'
    SPRINKLE_START = 'sprinkle_start'
    SPRINKLE_ON = 'sprinkle_on'
    SPRINKLE_OFF = 'sprinkle_off'
    SLEEP = "sleep_now"
    SWITCH_BROKER_DEBUG = "switch_broker_debug"
    SWITCH_BROKER_PROD = "switch_broker_prod"
    POWER_OFF = "power_off"


# Device-specific schedule configuration
class IOTDeviceSchedule(BaseModel):

    device = models.ForeignKey(IOTDevice, on_delete=models.CASCADE)

    schedule_type = models.CharField(max_length=100, choices=ScheduleTypes.choices,
                                     default=ScheduleTypes.SPRINKLE)
    # If only hour is populated, this means every day on that hour.  if only minute, every hour on that
    # minute.  Only one of the two should be populated
    hour = models.IntegerField()
    minute = models.IntegerField()

    # this will be managed by the automation
    next_execution = models.DateTimeField(auto_now=False)

    # whether to consider this schedule
    active = models.BooleanField(default=False)

    # minimum time to wait between executions of this schedule
    minimum_hours_between_executions = models.IntegerField(default=168)

    def __str__(self):
        return f"{self.device} - {self.schedule_type}"


# log of scheduled actions
class IOTDeviceScheduleExecution(BaseModel):

    iot_device_schedule = models.ForeignKey(IOTDeviceSchedule, on_delete=models.CASCADE)

    schedule_type = models.CharField(max_length=100, choices=ScheduleTypes.choices,
                                     default=ScheduleTypes.SPRINKLE)

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
    supply_voltage = models.FloatField(null=True)  # TODO: do we need this?
    water_pressure_ticks = models.IntegerField(null=True)

    def __str__(self):
        return f"{self.device.name} - {self.created.strftime('%Y-%m-%d %H:%M:%S')} | {self.supply_voltage} V | " \
               f"{self.water_pressure_ticks} water pressure ticks"

    def get_percentage_full(self):
        if (self.device.cal_low_pressure_ticks is None or
                self.device.cal_high_pressure_ticks is None or
                self.water_pressure_ticks is None):
            return 0

        diff_between_cal_points = self.device.cal_high_pressure_ticks - self.device.cal_low_pressure_ticks
        diff_between_measured_and_low_cal = self.water_pressure_ticks - self.device.cal_low_pressure_ticks

        return diff_between_measured_and_low_cal / diff_between_cal_points * 100

# store global settings - not sure what exactly, but it might be useful
class Setting(BaseModel):
    key = models.TextField()
    value = models.TextField()

# server to device commands
class ServerToDeviceCommandLog(BaseModel):
    device = models.ForeignKey(IOTDevice, on_delete=models.CASCADE)
    command = models.CharField(max_length=100, choices=ServerToDeviceCommand.choices,)
    command_id = models.UUIDField(auto_created=True, default=uuid.uuid4, editable=False)
    body = models.JSONField()

    def __str__(self):
        return f"Device '{self.device.name}' (ID {self.device.device_id}), Command: {self.command}"
