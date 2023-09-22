import requests
from sprinkler.classes.precip_observations import PrecipObservations
from sprinkler.models import RainLog
import json
import os


def convert_mm_to_in(length_in_mm):
    if length_in_mm:
        return length_in_mm * 0.0393701
    return 0


def record_precip_observations(test=False) -> PrecipObservations | None:
    """
    Fetch precip observations from weather data source and upsert them to the db

    :param test: if true, use local test data
    :return:
    """
    precip_observations = get_precip_observations(test)

    # ensure each observation is captured in the database
    if precip_observations:
        for precip_event in precip_observations.precip_events:

            # check for a precip event with this start time.  if we have it, update its data
            matching_rain_logs: list[RainLog] = RainLog.objects.filter(start_time=precip_event.start)

            if matching_rain_logs:
                matching_rain_log = matching_rain_logs[0]
                matching_rain_log.end_time = precip_event.end
                matching_rain_log.total_amount_inches = convert_mm_to_in(precip_event.total_mm)
                matching_rain_log.save()
            else:
                new_rain_log = RainLog(start_time=precip_event.start, end_time=precip_event.end,
                                       total_amount_inches=convert_mm_to_in(precip_event.total_mm))
                new_rain_log.save()

    return precip_observations


def get_precip_observations(test=False) -> PrecipObservations | None:
    """
    Fetch a report of precipitation specifically for KOJC from weather.gov
    :return:
    """

    if test:
        this_dir = os.path.dirname(os.path.realpath(__file__))
        parent_dir = os.path.dirname(this_dir)
        test_file_path = os.path.join(parent_dir, 'resources', 'precip_observations_test_data.json')
        with open(test_file_path) as test_file:
            data = json.load(test_file)
            return PrecipObservations(raw_data=data)

    ret_val = None
    url = 'https://api.weather.gov/stations/KOJC/observations'
    response = requests.get(url)

    if response.ok:
        data = response.json()
        ret_val = PrecipObservations(raw_data=data)

    return ret_val
