from sprinkler.models import IOTDevice


def create_device(device_id=0, device_name="test", cal_low_pressure_ticks=50, cal_high_pressure_ticks=100) -> IOTDevice:
    device = IOTDevice.objects.create(name=device_name,
                                      minimum_water_interval_hours=168,
                                      watering_length_minutes=10,
                                      watering_wait_minutes=5,
                                      watering_repetitions=2,
                                      device_id=device_id,
                                      cal_low_ticks_voltage=100,
                                      cal_high_ticks_voltage=700,
                                      cal_low_voltage=10,
                                      cal_high_voltage=13,
                                      cal_low_pressure_ticks=cal_low_pressure_ticks,
                                      cal_high_pressure_ticks=cal_high_pressure_ticks)

    return device
