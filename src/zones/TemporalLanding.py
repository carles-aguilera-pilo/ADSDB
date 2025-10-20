from zones.AZone import AZone

class TemporalLanding(AZone):
    def __init__(self, bucket_origin, bucket_destination):
        self.bucket_origin = bucket_origin
        self.bucket_destination = bucket_destination

    def treatData(self, dataobj):
        dataobj.save(self.bucket_destination)
        
