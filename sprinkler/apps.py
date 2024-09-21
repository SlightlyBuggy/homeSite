from django.apps import AppConfig


class SprinklerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sprinkler'

    # TODO: for testing, either don't connect to the broker
    # or use test topics
    # or have a test instance of the broker?
    def ready(self):
        from sprinkler import mqtt

        mqtt.client.loop_start()
