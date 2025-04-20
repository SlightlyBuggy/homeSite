import requests
from sprinkler.classes.PrecipObservations import PrecipObservations
from sprinkler.models import RainLog
from sprinkler.service import schedule_service
from datetime import timedelta


def convert_mm_to_in(length_in_mm):
    if length_in_mm:
        return length_in_mm * 0.0393701
    return 0


def get_and_record_precip_observations(test_observations=None) -> PrecipObservations | None:
    """
    Fetch precip observations from weather data source and upsert them to the db

    :param test_observations: raw observation data for test
    :return:
    """
    precip_observations: PrecipObservations | None = get_precip_observations(test_observations)

    # ensure each observation is captured in the database
    if precip_observations:
        new_log_created = create_rain_logs_from_precip_observations(precip_observations=precip_observations)

        # TODO: a better solution would be to have the creation timestamp in the rain log object
        # then we can have a function like update_device_schedules_based_on_precip() which queries
        # the DB and looks for any logs created very recently
        if new_log_created:
            schedule_service.update_sprinkle_schedules()

    return precip_observations


def create_rain_logs_from_precip_observations(precip_observations) -> bool:
    new_log_created = False

    # due to no rising edge.  need to give it a start time
    for precip_event in precip_observations.precip_events:

        # check for a precip event with this start time.  if we have it, update its data
        matching_rain_logs: list[RainLog] = []
        if precip_event.start:
            matching_rain_logs: list[RainLog] = RainLog.objects.filter(start_time=precip_event.start)

        if matching_rain_logs:
            matching_rain_log = matching_rain_logs[0]
            matching_rain_log.end_time = precip_event.end
            matching_rain_log.total_amount_inches = convert_mm_to_in(precip_event.total_mm)
            matching_rain_log.save()
        else:
            # heal case where there is no start time
            if not precip_event.start and precip_event.end:
                precip_event.start = precip_event.end + timedelta(hours=-1)
            new_rain_log = RainLog(start_time=precip_event.start, end_time=precip_event.end,
                                   total_amount_inches=convert_mm_to_in(precip_event.total_mm))
            new_rain_log.save()
            new_log_created = True

    return new_log_created


# TODO: use a different weather API.  This one is awful.  
def get_precip_observations(test_raw_data=None) -> PrecipObservations | None:
    """
    Fetch a report of precipitation specifically for KOJC from weather.gov
    :return:
    """

    if test_raw_data:
        return PrecipObservations(raw_data=test_raw_data)

    ret_val = None
    url = 'https://api.weather.gov/stations/KOJC/observations'
    response = requests.get(url)

    if response.ok:
        data = response.json()
        ret_val = PrecipObservations(raw_data=data)

    return ret_val
