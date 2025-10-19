from zones.PersistentLanding import PersistentLanding


persistent_landing = PersistentLanding(supported_modals = ["images", "audios", "texts"], bucket_origin = "persistent-zone", bucket_destination = "formatted-zone")
persistent_landing.execute()