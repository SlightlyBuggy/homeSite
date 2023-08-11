import requests
from sprinkler.classes.precip_observations import PrecipObservations
import json
import os


def get_precip_observations(test=False) -> PrecipObservations | None:
    """
    Fetch a report of precipitation
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
