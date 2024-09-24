import requests
from sprinkler.classes.precip_observations import PrecipObservations
from sprinkler.models import RainLog
from sprinkler.service import schedule_service
import json
import os


def convert_mm_to_in(length_in_mm):
    if length_in_mm:
        return length_in_mm * 0.0393701
    return 0


def get_and_record_precip_observations(test_file=None) -> PrecipObservations | None:
    """
    Fetch precip observations from weather data source and upsert them to the db

    :param test_file: path to local data
    :return:
    """
    precip_observations: PrecipObservations | None = get_precip_observations(test_file)

    # ensure each observation is captured in the database
    if precip_observations:
        create_rain_logs_from_precip_observations(precip_observations=precip_observations)

        #TODO: need way to manually override next schedule without automation fighting
        schedule_service.update_sprinkle_schedules()

    return precip_observations


def create_rain_logs_from_precip_observations(precip_observations):
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


def get_precip_observations(test_file=None) -> PrecipObservations | None:
    """
    Fetch a report of precipitation specifically for KOJC from weather.gov
    :return:
    """

    if test_file:
        if not os.path.exists(test_file):
            raise FileNotFoundError(f"cannot find test file {test_file}")
        with open(test_file) as test_file:
            data = json.load(test_file)
            return PrecipObservations(raw_data=data)

    ret_val = None
    url = 'https://api.weather.gov/stations/KOJC/observations'
    response = requests.get(url)

    if response.ok:
        data = response.json()
        ret_val = PrecipObservations(raw_data=data)

    return ret_val
