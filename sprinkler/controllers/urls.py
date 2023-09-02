from django.urls import path
from sprinkler.controllers import device_command, schedule, precipitation, mqtt

urlpatterns = [
    path('status', device_command.status, name='test_device_command_status'),
    path('sprinkle_start', device_command.sprinkle_start, name='test_device_command_sprinkle_start'),
    path('sprinkle_on', device_command.sprinkle_on, name='sprinkle_on'),
    path('sprinkle_off', device_command.sprinkle_off, name='sprinkle_off'),
    path('sleep_now', device_command.sleep_now, name='sleep_now'),
    path('switch_broker_debug', device_command.switch_broker_debug, name='switch_broker_debug'),
    path('switch_broker_prod', device_command.switch_broker_prod, name='switch_broker_prod'),
    path('execute_scheduled_tasks', schedule.execute_scheduled_tasks, name='execute_scheduled_tasks'),
    path('get_precip_observations', precipitation.get_precip_observations, name='get_precip_observations'),
    path('publish', mqtt.publish_message, name='publish'),
]
