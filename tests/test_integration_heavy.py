import os
import pytest
from md2kindle.app.pipeline import run
from md2kindle.core.config.settings import AppConfig

@pytest.mark.skipif(not os.getenv("RUN_HEAVY_TESTS"), reason="Prueba de fuego lenta. Set RUN_HEAVY_TESTS=true para ejecutar.")
def test_kaguya_mixed_volume_integration():
    """
    Prueba de fuego: Kaguya-sama Vol 1-2 en es-la.
    Este test valida:
    - Descarga mixta (es-la + en)
    - Auditoría de integridad
    - Conversión KCC
    - Estructura de archivos final
    """
    from md2kindle.core.models.pipeline import PipelineContext, MangaContext, DownloadRange, DeliveryOptions
    from md2kindle.core.config.settings import load_config
    
    config = load_config()
    
    # Kaguya-sama UUID
    manga_url = "https://mangadex.org/title/37f5cce0-8070-4ada-96e5-fa24b1bd4ff9"
    manga_id = "37f5cce0-8070-4ada-96e5-fa24b1bd4ff9"
    
    ctx = PipelineContext(
        manga=MangaContext(
            url=manga_url,
            title="Kaguya Integration Test",
            lang="es-la",
            author="Aka Akasaka",
            manga_uuid=manga_id
        ),
        range=DownloadRange(
            mode="v",
            start="1",
            end="2",
            skip_oneshots=True
        ),
        delivery=DeliveryOptions(
            telegram=False,
            r2=False
        ),
        silent=False
    )


    
    # Ejecutar pipeline
    run(params=ctx, app_config=config)
    
    # Verificar que existen los archivos (MOBI o EPUB) en la carpeta de salida de KCC
    manga_output_base = os.path.join(config.output_folder_kcc, "Kaguya Integration Test")
    
    # KCC genera archivos con formato "[Manga Title] [Vol X].mobi"
    expected_vol1 = os.path.join(manga_output_base, "Vol 1", "Kaguya Integration Test Vol 1.mobi")
    expected_vol2 = os.path.join(manga_output_base, "Vol 2", "Kaguya Integration Test Vol 2.mobi")
    
    # KCC puede generar .epub si así está configurado
    found1 = os.path.exists(expected_vol1) or os.path.exists(expected_vol1.replace(".mobi", ".epub"))
    found2 = os.path.exists(expected_vol2) or os.path.exists(expected_vol2.replace(".mobi", ".epub"))
    
    assert found1, f"Vol 1 no encontrado en {manga_output_base}"
    assert found2, f"Vol 2 no encontrado en {manga_output_base}"


