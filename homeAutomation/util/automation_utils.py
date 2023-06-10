import json
from django.http import JsonResponse
from ..mqtt import client as mqtt_client
from ..models import RainLog, WaterLog
import datetime


def send_mqtt_message(topic, body):
    # TODO: validate message
    rc, mid = mqtt_client.publish(topic, body)
    return JsonResponse({'code': rc})


def get_last_watering_and_rain_status() -> tuple[any, bool]:

    last_rain_log = RainLog.objects.all().order_by('start_time')

    if len(last_rain_log) == 0:
        return None, False

    last_rain: RainLog = last_rain_log[0]

    # if this is true, it must still be raining
    currently_raining = last_rain.start_time and not last_rain.end_time

    return last_rain.end_time, currently_raining
