from django.test import TestCase
import sprinkler.service.weather_service as weather_service
from sprinkler.models import RainLog
import os


class WeatherServiceTest(TestCase):

    @staticmethod
    def get_test_file_path():
        this_dir = os.path.dirname(os.path.realpath(__file__))
        parent_dir = os.path.dirname(this_dir)
        test_file_path = os.path.join(parent_dir, 'resources', 'precip_observations_test_data.json')
        return test_file_path

    def test_get_and_record_precip_observations_no_schedules(self):
        """
        Verify the test response from the precip endpoint is properly translated to DB objects
        """

        weather_service.get_and_record_precip_observations(test_file=self.get_test_file_path())

        rain_logs: list[RainLog] = RainLog.objects.all().order_by('-start_time')

        # the test data should yield
        self.assertEqual(len(rain_logs), 2)

        # the most recent log should be in progress, i.e. no end time
        most_recent_log = rain_logs[0]
        self.assertEqual(most_recent_log.end_time, None)
        self.assertNotEqual(most_recent_log.start_time, None)
        self.assertNotEqual(most_recent_log.total_amount_inches, None)

        # the earlier log should record a complete event, i.e. has an end time
        earlier_log = rain_logs[1]
        self.assertNotEqual(earlier_log.end_time, None)
        self.assertNotEqual(earlier_log.start_time, None)
        self.assertNotEqual(most_recent_log.total_amount_inches, None)
        self.assertTrue(earlier_log.end_time > earlier_log.start_time)

    def test_get_and_record_precip_observations_with_schedules(self):
        """
        Verify that schedules are updated appropriately given a rain event
        """
        #TODO: set up a test device and schedule.  verify a rain event appropriately bumps out the next exeuction

