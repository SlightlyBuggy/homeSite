from sprinkler.models import RainLog
from datetime import datetime, timedelta, timezone


def create_rain_log_finished_one_hour_ago() -> RainLog:

    now = datetime.now(tz=timezone.utc)
    rain_start = now + timedelta(days=-1)
    rain_end = now + timedelta(hours=-1)

    rain_log = RainLog.objects.create(start_time=rain_start, end_time=rain_end, total_amount_inches=1)

    return rain_log


def create_rain_log_in_progress() -> RainLog:
    now = datetime.now(tz=timezone.utc)
    rain_start = now + timedelta(hours=-1)

    rain_log = RainLog.objects.create(start_time=rain_start, total_amount_inches=1)

    return rain_log
