from src.zones.AZone import AZone

class FormattedZone(AZone):
    def __init__(self, supported_modals, bucket_origin, bucket_destination):
        self.bucket_origin = bucket_origin
        self.bucket_destination = bucket_destination
        self.supported_modals = supported_modals

    def treatData(self, dataobj):
        dataobj.clean()
        dataobj.save(self.bucket_destination)
    