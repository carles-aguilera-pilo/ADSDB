from src.zones.AZone import AZone

class PersistentLanding(AZone):
    def __init__(self, supported_modals, bucket_origin, bucket_destination):
        self.supported_modals = supported_modals
        self.bucket_origin = bucket_origin
        self.bucket_destination = bucket_destination

    def treatData(self, dataobj):
        dataobj.format()
        dataobj.save(self.bucket_destination)
    