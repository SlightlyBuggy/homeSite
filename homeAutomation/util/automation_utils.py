import json
from django.http import JsonResponse
from ..mqtt import client as mqtt_client
from ..models import RainLog, SprinklerLog, IOTDeviceSchedule
import datetime

COMMAND_TOPIC = 'device_commands'
MESSAGE_TOPIC = 'device_messages'
WATERING_SCHEDULE_PUSH_MINUTES = 360
MINUTES_IN_DAY = 1440


def send_mqtt_message(topic, body):
    # TODO: validate message
    rc, mid = mqtt_client.publish(topic, body)
    return JsonResponse({'code': rc})


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
    if len(last_rain_log) > 0:
        last_rain: RainLog = last_rain_log[0]
        currently_raining = last_rain.start_time and not last_rain.end_time
        last_rain_end = last_rain.end_time

    if len(last_sprinkler_log) > 0:
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


def get_next_scheduled_daily_time(schedule: IOTDeviceSchedule, starting_at, interval_minutes=None):
    """
    Given a schedule and an optinal interval,
    :return: datetime.datetime of the next scheduled run
    """
    # set the inverval from the schedule or the override property
    minutes_till_next_scheduled_event = interval_minutes if interval_minutes else schedule.interval_minutes

    scheduled_dt = starting_at + datetime.timedelta(0, 0, 0, 0, minutes_till_next_scheduled_event)

    # make sure the schedule's hour/minute are respected
    if schedule.hour:
        scheduled_dt = scheduled_dt.replace(hour=schedule.hour)
    if schedule.minute:
        scheduled_dt = scheduled_dt.replace(minute=schedule.minute)

    # if the new time is before the interval has elapsed, push forward 1 day
    if scheduled_dt < starting_at + datetime.timedelta(0, 0, 0, 0, schedule.interval_minutes):
        scheduled_dt = scheduled_dt + datetime.timedelta(0, 0, 1)

    return scheduled_dt
