from datetime import datetime, timezone, timedelta
from sprinkler.classes.PrecipObservations import PrecipObservations


def build_feature(timestamp=datetime.now(timezone.utc), precipitation_last_hour=10):

    return {'properties': {
        'precipitationLastHour': {'value': precipitation_last_hour},
        'timestamp': timestamp
    }}


def build_raw_data_from_features(features):

    # the existing API has things sorted by timestamp with the most recent first
    features.sort(key=lambda feature: feature['properties']['timestamp'], reverse=True)
    return {'features': features}


def build_observation_ongoing_rain():
    now = datetime.now(timezone.utc)
    one_hour_ago = now + timedelta(hours=-1)

    ongoing_rain_feature = build_feature(timestamp=one_hour_ago)
    raw_data = build_raw_data_from_features([ongoing_rain_feature])
    return raw_data


def build_raw_precip_data_rain_ended_one_hour_ago():
    now = datetime.now(timezone.utc)
    one_hour_ago = now + timedelta(hours=-1)
    rain_ended_feature = build_feature(timestamp=one_hour_ago, precipitation_last_hour=0)

    two_hours_ago = now + timedelta(hours=-1)
    last_rain_feature = build_feature(timestamp=two_hours_ago, precipitation_last_hour=1)

    raw_data = build_raw_data_from_features([rain_ended_feature, last_rain_feature])
    return raw_data


def build_raw_precip_data_rain_ended_two_hours_ago_and_ongoing():
    now = datetime.now(timezone.utc)

    one_hour_ago = now + timedelta(hours=-1)
    ongoing_rain_feature = build_feature(timestamp=one_hour_ago, precipitation_last_hour=1)

    two_hours_ago = now + timedelta(hours=-2)
    past_rain_ended_feature = build_feature(timestamp=two_hours_ago, precipitation_last_hour=0)

    three_hours_ago = now + timedelta(hours=-3)
    past_rain_feature = build_feature(timestamp=three_hours_ago, precipitation_last_hour=1)

    raw_data = build_raw_data_from_features([ongoing_rain_feature, past_rain_ended_feature,
                                             past_rain_feature])
    return raw_data


def build_raw_precip_data_rain_ended_10_days_ago():

    now = datetime.now(timezone.utc)

    ten_days_ago = now + timedelta(days=-10)
    no_rain_feature = build_feature(timestamp=ten_days_ago, precipitation_last_hour=0)

    ten_days_and_one_hour_ago = now + timedelta(days=-10, hours=-1)
    last_rain_feature = build_feature(timestamp=ten_days_and_one_hour_ago, precipitation_last_hour=1)

    raw_data = build_raw_data_from_features([no_rain_feature, last_rain_feature])
    return raw_data
