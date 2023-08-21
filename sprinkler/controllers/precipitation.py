from sprinkler.service import weather_service
from django.http import JsonResponse


def get_precip_observations(request):
    precip_observations = weather_service.get_precip_observations(test=True)
    print("Fetched test precipitation report")
    print(precip_observations)

    return JsonResponse({'precip_events': precip_observations.precip_events})