from zones.AZone import AZone

class TemporalLanding(AZone):
    NEXT_BUCKET = "persistent-zone"

    def __init__(self):
        self