from src.zones.TemporalLanding import TemporalLanding
from src.zones.PersistentLanding import PersistentLanding
from src.zones.FormattedZone import FormattedZone
from src.zones.TrustedZone import TrustedZone
from src.zones.DataCollection import DataCollection

SUPPORTED_MODALS = ["images", "audios", "texts"] # These are the data modals contemplated in our pipeline. Should this be extended. See Readme for information about how to do it.
"""
print("Starting data collection...")
DataCollection.collect_data()
DataCollection.upload_data("temporal-landing-zone")

print("Starting data processing pipeline...")
print("-> Temporal Landing Zone")
temporal_landing = TemporalLanding(supported_modals = SUPPORTED_MODALS, bucket_origin = "temporal-landing-zone", bucket_destination = "persistent-landing-zone")
temporal_landing.execute()

print("-> Persistent Landing Zone")
persistent_landing = PersistentLanding(supported_modals = SUPPORTED_MODALS, bucket_origin = "persistent-landing-zone", bucket_destination = "formatted-zone")
persistent_landing.execute()

print("-> Formatted Zone")
formatted_zone = FormattedZone(supported_modals = SUPPORTED_MODALS, bucket_origin = "formatted-zone", bucket_destination = "trusted-zone")
formatted_zone.execute()
"""
print("-> Trusted Zone")
trusted_zone = TrustedZone(supported_modals = SUPPORTED_MODALS, bucket_origin = "trusted-zone", bucket_destination="exploitation-zone")
trusted_zone.execute()