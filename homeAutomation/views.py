import json
from django.http import JsonResponse
from homeAutomation.mqtt import client as mqtt_client


def publish_message(request):
    request_data = json.loads(request.body)
    rc, mid = mqtt_client.publish(request_data['topic'], request_data['msg'])
    return JsonResponse({'code': rc})


def test_device_message(request):
    rc, mid = mqtt_client.publish('device_messages', 'test device message sent')
    return JsonResponse({'code': rc})


def test_device_command(request):
    rc, mid = mqtt_client.publish('device_commands', 'test device command sent')
    return JsonResponse({'code': rc})