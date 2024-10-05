import copy


class PrecipEvent:

    def __init__(self, start=None, end=None, total_mm=None):
        self.start = start
        self.end = end
        self.total_mm = total_mm


class PrecipObservations:

    def __init__(self, raw_data):

        self.raw_data = raw_data
        self.precip_events: list[PrecipEvent] = []

        self.build_precip_events()

    def build_precip_events(self):
        precip_observations = self.raw_data['features']

        # walk backwards through the observations, building precip events
        # when we have a record that has precip in the last hour, that is the end of the rain event
        # add to the total precip until we get to a record that does not have precip in the last hour
        # if the very first record has a precip event, this is an ongoing precip event, so create an observation without
        # an end time

        precip_prior_observation = 0

        for idx, observation in enumerate(precip_observations):
            precip_this_observation = observation['properties']['precipitationLastHour']['value']
            timestamp = observation['properties']['timestamp']

            # detect falling edge (end of precip event)
            if precip_this_observation and not precip_prior_observation:

                precip_record = PrecipEvent(total_mm=precip_this_observation)

                # if this is the first index, this could be an ongoing precip event, so we don't want an end
                if idx != 0:
                    precip_record.end = timestamp

                self.precip_events.append(precip_record)

            # detect continuing precip event
            if precip_this_observation and precip_prior_observation:
                self.precip_events[-1].total_mm += precip_this_observation

            # detect rising edge (start of precip event)
            if not precip_this_observation and precip_prior_observation:
                self.precip_events[-1].start = timestamp

            precip_prior_observation = precip_this_observation
