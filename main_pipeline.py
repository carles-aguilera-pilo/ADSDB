
try:
    from notebooks.landing_zone.Alanding import LandingZone
    from notebooks.formatted_zone.Aformated import FormatedZone
    from notebooks.trusted_zone.Atrusted import TrustedZone
    from notebooks.landing_zone.data_collection import DataCollection


    from notebooks.landing_zone.temporal_zone import TemporalZone
    from notebooks.landing_zone.persistent_zone import PersistentZone


    from notebooks.formatted_zone.formated_zone_audio import FormatedZoneAudio
    from notebooks.formatted_zone.formated_zone_images import FormatedZoneImages
    from notebooks.formatted_zone.formated_zone_text import FormatedZoneText


    from notebooks.trusted_zone.trusted_zone_audio import TrustedZoneAudio
    from notebooks.trusted_zone.trusted_zone_images import TrustedZoneImages
    from notebooks.trusted_zone.trusted_zone_text import TrustedZoneText
    
    print("=== INICIANDO PIPELINE DE PROCESAMIENTO DE DATOS ===")
    
    # EXECUTE THE LANDING ZONE
    print("\n1. Executing Landing Zone...")
    landing_zone = LandingZone(DataCollection())
    landing_zone.executar()
    
    landing_zone.set_strategy(TemporalZone())
    landing_zone.executar()
    
    landing_zone.set_strategy(PersistentZone())
    landing_zone.executar()
    
    # EXECUTE THE FORMATTED ZONE
    #print("\n2. Executing Formatted Zone...")
    #formated_zone = FormatedZone(FormatedZoneAudio())
    #formated_zone.executar()
    
    #formated_zone.set_strategy(FormatedZoneImages())
    #formated_zone.executar()
    
    #formated_zone.set_strategy(FormatedZoneText())
    #formated_zone.executar()
    
    # EXECUTE THE TRUSTED ZONE
    #print("\n3. Executing Trusted Zone...")
    #trusted_zone = TrustedZone(TrustedZoneAudio())
    #trusted_zone.executar()
    
    #trusted_zone.set_strategy(TrustedZoneImages())
    #trusted_zone.executar()
    
    #trusted_zone.set_strategy(TrustedZoneText())
    #trusted_zone.executar()
    
    #print("\n=== PIPELINE COMPLETED SUCCESSFULLY ===")
    
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all modules are available")
except Exception as e:
    print(f"Error during execution: {e}")
    import traceback
    traceback.print_exc()