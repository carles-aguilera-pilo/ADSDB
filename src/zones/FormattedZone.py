from src.zones.AZone import AZone

class FormattedZone(AZone):
    def __init__(self, bucket_origin, bucket_destination):
        self.bucket_origin = bucket_origin
        self.bucket_destination = bucket_destination
        self.supported_modals = ["images", "audios", "texts"] # TODO: Change to according values JOWI

    def treatData(self, dataobj):
        dataobj.clean() # Applies persistent-formatted transformation on data
        dataobj.save(self.bucket_destination)
    