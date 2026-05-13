import os
import logging
import boto3
from botocore.exceptions import ClientError

from md2kindle.core.config import APP_CONFIG, AppConfig

logger = logging.getLogger(__name__)

def get_r2_client(app_config: AppConfig | None = None):
    config = app_config or APP_CONFIG
    account_id = config.r2_account_id
    access_key = config.r2_access_key_id
    secret_key = config.r2_secret_access_key

    if not all([account_id, access_key, secret_key]):
        logger.error("No se configuraron las credenciales de Cloudflare R2 (Account ID / Access Key / Secret Key).")
        return None

    # URL del endpoint de R2 para tu cuenta
    endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

    try:
        s3_client = boto3.client(
            service_name="s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="auto",  # R2 requiere 'auto'
        )
        return s3_client
    except Exception as e:
        logger.error(f"Error al inicializar cliente R2: {e}")
        return None

def send_to_r2(filepath: str, manga: str, vol: str, app_config: AppConfig | None = None) -> str | None:
    """
    Sube un archivo a Cloudflare R2 y retorna una URL presignada.
    
    Args:
        filepath: Ruta local del archivo a subir.
        manga: Nombre del manga (para organizar en carpetas).
        vol: Nombre del volumen o capítulo.
        app_config: Configuración de la aplicación.
        
    Returns:
        URL presignada válida por 7 días o None si falla.
    """
    if not os.path.exists(filepath):
        logger.error(f"Archivo no encontrado para subir a R2: {filepath}")
        return None

    config = app_config or APP_CONFIG
    bucket_name = config.r2_bucket_name
    if not bucket_name:
        logger.error("No se configuró el nombre del bucket R2 (R2_BUCKET_NAME).")
        return None

    s3 = get_r2_client(app_config=config)
    if not s3:
        return None

    # Construimos la llave de objeto (Ruta en el bucket)
    # Ej: "Solo Leveling/Solo Leveling Vol 1.mobi"
    filename = os.path.basename(filepath)
    object_key = f"{manga}/{filename}"

    logger.info(f"Subiendo {filename} a Cloudflare R2...")

    try:
        s3.upload_file(filepath, bucket_name, object_key)
        logger.info(f"Subida exitosa: {object_key}")
        
        # Generar Presigned URL (expira en 7 días = 604800 segundos)
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_key},
            ExpiresIn=604800
        )
        
        return url

    except ClientError as e:
        logger.error(f"Error de subida R2: {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado al subir a R2: {e}")
        return None
