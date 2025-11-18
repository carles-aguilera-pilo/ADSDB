from src.zones.AZone import AZone

class TrustedZone(AZone):
    def __init__(self, supported_modals, bucket_origin, bucket_destination):
        self.supported_modals = supported_modals
        self.bucket_origin = bucket_origin
        self.bucket_destination = bucket_destination

    def treatData(self, dataobj):
        dataobj.embed()
        dataobj.save(self.bucket_destination, chromadb=True, collection_name="multimodal_collection")


    