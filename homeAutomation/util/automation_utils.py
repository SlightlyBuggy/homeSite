import json
from django.http import JsonResponse
from ..mqtt import client as mqtt_client
from ..models import RainLog, SprinklerLog
import datetime

COMMAND_TOPIC = 'device_commands'
MESSAGE_TOPIC = 'device_messages'


def send_mqtt_message(topic, body):
    # TODO: validate message
    rc, mid = mqtt_client.publish(topic, body)
    return JsonResponse({'code': rc})


def get_last_watering_and_status(device_id) -> tuple[any, bool]:
    """
    Determine what the end of the most recent rain or watering event is, and whether a watering event is in
    progress
    :param device_id: id of device to check
    :return: tuple of last_water_event_end, water_event_in_progress
    """

    last_rain_log: list[RainLog] = RainLog.objects.all().order_by('-start_time')[:1]
    last_sprinkler_log: list[SprinklerLog] = SprinklerLog.objects.filter(device_id=device_id).order_by('-start_time')[:1]

    currently_raining = False
    currently_watering = False

    last_rain_end = None
    last_water_end = None

    # extract end of last event and current status for both the rain and water logs
    if len(last_rain_log) > 0:
        last_rain: RainLog = last_rain_log[0]
        currently_raining = last_rain.start_time and not last_rain.end_time
        last_rain_end = last_rain.end_time

    if len(last_sprinkler_log) > 0:
        last_watering: SprinklerLog = last_sprinkler_log[0]
        currently_watering = last_watering.start_time and not last_watering.end_time
        last_water_end = last_watering.end_time

    # if we have times for both end events, use the most recent
    if last_rain_end and last_water_end:
        last_water_event_end = last_rain_end if last_rain_end > last_water_end else last_water_end

    # if that didn't work, set it to whatever value isn't None
    if not last_water_event_end:
        last_water_event_end = last_rain_end if last_rain_end else last_water_end if last_water_end else None

    return last_water_event_end, currently_raining or currently_watering


def add_minutes_to_dt(dt: datetime.datetime, minutes: int):
    """
    Add a certain number of minutes to a datetime
    :param dt: datetime.datetime object
    :param minutes: number of minutes
    :return:
    """
    return dt + datetime.timedelta(0, 0, 0, 0, minutes)
