"""homeAutomation URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from sprinkler import views

app_name = 'sprinkler'
urlpatterns = [
    path('publish', views.publish_message, name='publish'),
    path('test_device_command_status', views.test_device_command_status, name='test_device_command_status'),
    path('test_device_command_sprinkle_start', views.test_device_command_sprinkle_start,
         name='test_device_command_sprinkle_start'),
    path('get_precip_observations', views.get_precip_observations, name='get_precip_observations'),
    path('execute_scheduled_tasks', views.execute_scheduled_tasks, name='execute_scheduled_tasks')
]


