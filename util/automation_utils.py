import json
from django.http import JsonResponse
from sprinkler.models import RainLog, SprinklerLog, IOTDeviceSchedule, IOTDeviceScheduleExecution, IOTDevice
from datetime import datetime, timezone, timedelta


WATERING_SCHEDULE_PUSH_MINUTES = 360
MINUTES_IN_DAY = 1440
PSI_PER_PASCAL = 0.000145038


def get_last_watering_and_status(device_id) -> tuple[any, bool]:
    """
    Determine what the end of the most recent rain or watering event is, and whether a watering event is in
    progress
    :param device_id: id of device to check
    :return: tuple of last_sprinkler_or_rain_end, water_event_in_progress
    """

    last_rain_log: list[RainLog] = RainLog.objects.all().order_by('-start_time')[:1]
    last_sprinkler_log: list[SprinklerLog] = SprinklerLog.objects.filter(device_id=device_id).order_by('-start_time')[:1]

    currently_raining = False
    currently_sprinkling = False

    last_rain_end = None
    last_sprinkler_end = None
    last_sprinkler_or_rain_end = None

    # extract end of last event and current status for both the rain and water logs
    if last_rain_log:
        last_rain: RainLog = last_rain_log[0]
        currently_raining = last_rain.start_time and not last_rain.end_time
        last_rain_end = last_rain.end_time

    if last_sprinkler_log:
        last_watering: SprinklerLog = last_sprinkler_log[0]
        currently_sprinkling = last_watering.start_time and not last_watering.end_time
        last_sprinkler_end = last_watering.end_time

    # if we have times for both end events, use the most recent
    if last_rain_end and last_sprinkler_end:
        last_sprinkler_or_rain_end = last_rain_end if last_rain_end > last_sprinkler_end else last_sprinkler_end

    # if that didn't work, set it to whatever value isn't None
    if not last_sprinkler_or_rain_end:
        last_sprinkler_or_rain_end = last_rain_end if last_rain_end else last_sprinkler_end if last_sprinkler_end else None

    return last_sprinkler_or_rain_end, currently_raining or currently_sprinkling


def get_next_schd_using_start_time(schedule: IOTDeviceSchedule, starting_at, interval_minutes=None):
    """
    Given a schedule, starting time, and optional interval, compute the next time the schedule should be
    evaluated, respecting the start hour and minute
    :param: schedule: IOTDeviceSchedule
    :param: starting_at: datetime.datetime from which next execution should be calculated
    :return: datetime.datetime of the next scheduled run
    """
    # set the interval from the schedule or the override property
    minutes_till_next_scheduled_event = interval_minutes if interval_minutes else schedule.interval_minutes

    scheduled_dt = starting_at + timedelta(0, 0, 0, 0, minutes_till_next_scheduled_event)

    # make sure the schedule's hour/minute are respected
    if schedule.hour:
        scheduled_dt = scheduled_dt.replace(hour=schedule.hour)
    if schedule.minute:
        scheduled_dt = scheduled_dt.replace(minute=schedule.minute)

    # if there's no interval and no minute specified, set to x:00
    if not schedule.minute and not schedule.interval_minutes:
        scheduled_dt = scheduled_dt.replace(minute=0)

    scheduled_dt = scheduled_dt.replace(second=0)
    scheduled_dt = scheduled_dt.replace(microsecond=0)

    # if the new time is before the interval has elapsed, push forward 1 day
    if scheduled_dt < starting_at + timedelta(0, 0, 0, 0, minutes_till_next_scheduled_event):
        scheduled_dt = scheduled_dt + timedelta(0, 0, 1)

    current_dt = datetime.now(timezone.utc)

    # ensure the scheduled time is in the future.  this will heal cases where the server has been offline
    # for awhile or whatever
    while scheduled_dt < current_dt:
        scheduled_dt = scheduled_dt + timedelta(0, 0, 1)

    return scheduled_dt


def get_next_schd_using_interval(schedule: IOTDeviceSchedule):
    """
    Given a schedule, calculate the next scheduled time using the interval
    :param schedule: IOTDeviceSchedule
    :return: datetime.datetime of the next scheduled run
    """

    current_dt = datetime.now(timezone.utc)
    next_scheduled_dt = add_minutes_to_dt(schedule.next_execution, schedule.interval_minutes)
    while next_scheduled_dt < current_dt:
        next_scheduled_dt = add_minutes_to_dt(next_scheduled_dt, schedule.interval_minutes)

    return next_scheduled_dt


def add_minutes_to_dt(dt: datetime, minutes: int) -> datetime:
    """
    Add minutes to a datetime.datetime object
    :param dt: datetime.datetime object
    :param minutes: minutes to add
    :return: new datetime.datetime object with minutes added
    """

    return dt + timedelta(0, 0, 0, 0, minutes)


def build_schedule_execution(schedule: IOTDeviceSchedule, t: datetime, mqtt_response: JsonResponse) -> \
        IOTDeviceScheduleExecution:
    code = json.loads(mqtt_response.content)['code']
    schedule_execution = IOTDeviceScheduleExecution(iot_device_schedule_id=schedule.pk,
                                                    schedule_type=schedule.schedule_type,
                                                    start_time=t,
                                                    exit_code=code
                                                    )
    return schedule_execution


def get_voltage_from_ticks_and_cal(input_ticks: int, cal_low_ticks: int, cal_low_voltage: float,
                                   cal_high_ticks: int, cal_high_voltage: float) -> float:
    """
    Do a linear interpolation using cal data and input analog arduino ticks to get voltage
    :param input_ticks: raw a/d ticks from arduino
    :param cal_low_ticks: a/d ticks that correspond to cal_low_voltage
    :param cal_low_voltage: low voltage calibration point
    :param cal_high_ticks: a/d ticks that correspond to cal_high_voltage
    :param cal_high_voltage: high voltage calibration point
    :return:
    """

    voltage = (input_ticks - cal_low_ticks)*(cal_high_voltage - cal_low_voltage)/(cal_high_ticks - cal_low_ticks) + cal_low_voltage

    return voltage


def build_sprinkle_log(device: IOTDevice, start_time, end_time, water_qty_at_start_gallons,
                       water_qty_at_end_gallons) -> SprinklerLog:
    new_sprinkle_log = SprinklerLog(device=device, start_time=start_time, end_time=end_time,
                                    water_qty_at_start_gallons=water_qty_at_start_gallons,
                                    water_level_at_end_gallons=water_qty_at_end_gallons)
    return new_sprinkle_log
