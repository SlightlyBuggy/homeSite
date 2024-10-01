from django.apps import AppConfig
from django.conf import settings


class SprinklerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sprinkler'

    # TODO: for testing, either don't connect to the broker
    # or use test topics
    # or have a test instance of the broker?
    def ready(self):

        if settings.USE_REAL_MQTT_BROKER:
            from sprinkler.service import mqtt_service
            mqtt_service.initialize_and_start_real_mqtt()

        else:
            from sprinkler.service import mqtt_service
            mqtt_service.initialize_and_start_fake_mqtt()
