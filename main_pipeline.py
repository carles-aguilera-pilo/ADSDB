

import sys
import os

# Añadir las rutas de los módulos al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'notebooks', 'landing_zone'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'notebooks', 'formatted_zone'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'notebooks', 'trusted_zone'))

try:
    # Importar las clases principales
    from Alanding import LandingZone
    from Aformated import FormatedZone
    from Atrusted import TrustedZone
    
    # Importar las estrategias
    from data_collection import DataCollection
    from temporal_zone import TemporalZone
    from persistent_zone import PersistentZone
    from formated_zone_audio import FormatedZoneAudio
    from formated_zone_images import FormatedZoneImages
    from formated_zone_text import FormatedZoneText
    from trusted_zone_audio import TrustedZoneAudio
    from trusted_zone_images import TrustedZoneImages
    from trusted_zone_text import TrustedZoneText
    
    print("=== INICIANDO PIPELINE DE PROCESAMIENTO DE DATOS ===")
    
    # EJECUTAR LANDING ZONE
    print("\n1. Ejecutando Landing Zone...")
    landing_zone = LandingZone(DataCollection())
    landing_zone.executar()
    
    landing_zone.set_strategy(TemporalZone())
    landing_zone.executar()
    
    landing_zone.set_strategy(PersistentZone())
    landing_zone.executar()
    
    # EJECUTAR FORMATTED ZONE
    print("\n2. Ejecutando Formatted Zone...")
    formated_zone = FormatedZone(FormatedZoneAudio())
    formated_zone.executar()
    
    formated_zone.set_strategy(FormatedZoneImages())
    formated_zone.executar()
    
    formated_zone.set_strategy(FormatedZoneText())
    formated_zone.executar()
    
    # EJECUTAR TRUSTED ZONE
    print("\n3. Ejecutando Trusted Zone...")
    trusted_zone = TrustedZone(TrustedZoneAudio())
    trusted_zone.executar()
    
    trusted_zone.set_strategy(TrustedZoneImages())
    trusted_zone.executar()
    
    trusted_zone.set_strategy(TrustedZoneText())
    trusted_zone.executar()
    
    print("\n=== PIPELINE COMPLETADO EXITOSAMENTE ===")
    
except ImportError as e:
    print(f"Error de importación: {e}")
    print("Asegúrate de que todos los módulos estén disponibles")
except Exception as e:
    print(f"Error durante la ejecución: {e}")
    import traceback
    traceback.print_exc()
