from sprinkler.service import weather_service
from django.http import JsonResponse


def get_precip_observations(request):
    """
    Fetch precip observations from weather data source and store in the db
    :param request:
    :return: JsonResponse with precip events
    """
    precip_observations = weather_service.record_precip_observations(test=False)

    precip_events = []
    if precip_observations:
        precip_events = [vars(item) for item in precip_observations.precip_events]
    return JsonResponse({'precip_events': precip_events})
