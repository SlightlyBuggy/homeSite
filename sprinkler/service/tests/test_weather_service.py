from django.test import TestCase
import sprinkler.service.weather_service as weather_service
from sprinkler.models import RainLog
import os


class WeatherServiceTest(TestCase):

    @staticmethod
    def get_test_file_path():
        this_dir = os.path.dirname(os.path.realpath(__file__))
        parent_dir = os.path.dirname(this_dir)
        parent_of_parent = os.path.dirname(parent_dir)
        test_file_path = os.path.join(parent_of_parent, 'resources', 'precip_observations_test_data.json')
        return test_file_path

    def test_get_and_record_precip_observations_no_schedules(self):
        """
        Verify the test response from the precip endpoint is properly translated to DB objects
        """

        def assert_event_is_in_progress(rain_log: RainLog):
            self.assertIsNone(rain_log.end_time)
            self.assertIsNotNone(rain_log.start_time)
            self.assertIsNotNone(rain_log.total_amount_inches)

        def assert_event_is_complete(first_log: RainLog, second_log: RainLog):
            self.assertIsNotNone(first_log.end_time)
            self.assertIsNotNone(first_log.start_time)
            self.assertIsNotNone(second_log.total_amount_inches)
            self.assertTrue(first_log.end_time > first_log.start_time)

        weather_service.get_and_record_precip_observations(test_file=self.get_test_file_path())

        rain_logs: list[RainLog] = RainLog.objects.all().order_by('-start_time')

        # the test data should yield
        self.assertEqual(len(rain_logs), 2)

        # the most recent log should be in progress, i.e. no end time
        most_recent_log = rain_logs[0]
        assert_event_is_in_progress(most_recent_log)

        # the earlier log should record a complete event, i.e. has an end time
        earlier_log = rain_logs[1]
        assert_event_is_complete(earlier_log, most_recent_log)

    # TODO: create a test that verifies the automation overwrites the next execution when appropriate (next execution is too close to last precip)
    # TODO: create a test that verifies the automation does NOT overwrite the next execution when it should not (next execution is far enough away from last precip)

