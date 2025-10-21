from src.zones.AZone import AZone
from src.minio_connection import MinIOConnection

class TrustedZone(AZone):
    def __init__(self, supported_modals, bucket_origin, bucket_destination):
        self.supported_modals = supported_modals # There is a folder for each supported modal: Images, Audios and Texts
        self.bucket_origin = bucket_origin
        self.bucket_destination = bucket_destination

    def treatData(self, dataobj):
        dataobj.trust()
        dataobj.save(self.bucket_destination)


    