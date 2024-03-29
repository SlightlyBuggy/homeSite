from django.apps import AppConfig


class SprinklerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sprinkler'

    def ready(self):
        from sprinkler import mqtt

        mqtt.client.loop_start()
