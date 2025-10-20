from zones.AZone import AZone
from minio_connection import MinIOConnection

class PersistentLanding(AZone):
    def __init__(self, bucket_origin, bucket_destination):
        self.bucket_origin = bucket_origin
        self.bucket_destination = bucket_destination

    def treatData(self, dataobj):
        dataobj.clean() # Applies persistent-formatted transformation on data
        dataobj.save(self.bucket_destination)
    