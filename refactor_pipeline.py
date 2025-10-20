from src.zones.TemporalLanding import TemporalLanding
from src.zones.PersistentLanding import PersistentLanding
from src.zones.FormattedZone import FormattedZone
from src.zones.TrustedZone import TrustedZone
from src.zones.DataCollection import DataCollection

SUPPORTED_MODALS = ["images", "audios", "texts"] # These are the data modals contemplated in our pipeline. Should this be extended. See Readme for information about how to do it.

DataCollection.collect_data()
DataCollection.upload_data()

temporal_landing = TemporalLanding(bucket_origin = "temporal-landing", bucket_destination = "persistent-zone")
temporal_landing.execute()

persistent_landing = PersistentLanding(supported_modals = SUPPORTED_MODALS, bucket_origin = "persistent-zone", bucket_destination = "formatted-zone")
persistent_landing.execute()

formatted_zone = FormattedZone(bucket_origin = "formatted-zone", bucket_destination = "trusted-zone")
formatted_zone.execute()

#trusted_zone = TrustedZone(bucket_origin = "trusted-zone")
#formatted_zone.execute()