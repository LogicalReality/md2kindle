import os
import logging
import requests
import datetime
from md2kindle.core.config import APP_CONFIG, AppConfig

logger = logging.getLogger(__name__)

def log_download(manga: str, volume: str, lang: str, file_path: str, method: str, app_config: AppConfig | None = None) -> bool:
    """
    Registers a successful download and delivery in Cloudflare D1.
    
    Args:
        manga: Name of the manga
        volume: Volume or chapter identifier
        lang: Language of the downloaded manga
        file_path: Local path to the generated .mobi file to calculate its size
        method: Delivery method used ('r2', 'telegram', 'usb')
        app_config: Application configuration
        
    Returns:
        True if logged successfully, False otherwise.
    """
    config = app_config or APP_CONFIG
    account_id = config.d1_account_id
    db_id = config.d1_database_id
    api_token = config.d1_api_token

    if not all([account_id, db_id, api_token]):
        logger.debug("D1 credentials not fully configured. Skipping history logging.")
        return False

    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{db_id}/query"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    size_mb = 0.0
    if os.path.exists(file_path):
        size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)
        
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    payload = {
        "sql": "INSERT INTO downloads (manga, volume, lang, size_mb, method, delivered_at) VALUES (?, ?, ?, ?, ?, ?)",
        "params": [manga, volume, lang, size_mb, method, now_iso]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("success"):
            logger.info("Historial guardado en D1 exitosamente.")
            return True
        else:
            logger.error(f"Error de D1 API: {data.get('errors')}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Fallo al contactar la API de Cloudflare D1: {e}")
        return False
