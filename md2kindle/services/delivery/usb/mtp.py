import os
import subprocess
import threading
import queue
import time
import logging

logger = logging.getLogger(__name__)

try:
    import msvcrt
except ImportError:
    msvcrt = None

def copy_via_mtp(file_paths: list[str], manga_title: str) -> bool:
    """Copia una lista de archivos al Kindle usando MTP y espera a que aparezcan."""
    if not file_paths:
        return True

    abs_paths = [os.path.abspath(f) for f in file_paths]
    file_names = [os.path.basename(p) for p in abs_paths]
    safe_manga_title = manga_title.replace('"', '`"')
    ps_files_list = ", ".join([f'"{p}"' for p in abs_paths])
    ps_names_list = ", ".join([f'"{n}"' for n in file_names])
    
    ps_script = f"""
    $ErrorActionPreference = 'Stop'
    try {{
        Write-Host "Iniciando Shell de Windows..."
        $shell = New-Object -ComObject Shell.Application
        $computer = $shell.NameSpace(17)
        
        Write-Host "Buscando dispositivo Kindle..."
        $kindle = $computer.Items() | Where-Object {{ $_.Name -match "Kindle" }}
        if (-not $kindle) {{ 
            Write-Host "Error: No se encontró ningún dispositivo con nombre 'Kindle'."
            exit 1 
        }}
        
        Write-Host "Accediendo al almacenamiento interno..."
        $internal = $kindle.GetFolder.Items() | Where-Object {{ $_.Name -match "Internal Storage" -or $_.Name -match "Almacenamiento interno" }}
        if (-not $internal) {{ 
            Write-Host "Error: No se pudo acceder al almacenamiento del Kindle."
            exit 1 
        }}
        
        Write-Host "Buscando carpeta 'documents'..."
        $docs = $internal.GetFolder.Items() | Where-Object {{ $_.Name -match "documents" }}
        if (-not $docs) {{ 
            Write-Host "Error: No se encontró la carpeta 'documents'."
            exit 1 
        }}
        
        $mangaFolder = $docs.GetFolder.Items() | Where-Object {{ $_.Name -eq "Manga" }}
        if (-not $mangaFolder) {{
            Write-Host "Creando carpeta 'Manga'..."
            $docs.GetFolder.NewFolder("Manga")
            Start-Sleep -Seconds 1
            $mangaFolder = $docs.GetFolder.Items() | Where-Object {{ $_.Name -eq "Manga" }}
        }}
        
        $titleFolder = $mangaFolder.GetFolder.Items() | Where-Object {{ $_.Name -eq "{safe_manga_title}" }}
        if (-not $titleFolder) {{
            Write-Host "Creando carpeta para '{safe_manga_title}'..."
            $mangaFolder.GetFolder.NewFolder("{safe_manga_title}")
            Start-Sleep -Seconds 1
            $titleFolder = $mangaFolder.GetFolder.Items() | Where-Object {{ $_.Name -eq "{safe_manga_title}" }}
        }}
        
        $sourceFiles = @({ps_files_list})
        $targetNames = @({ps_names_list})
        
        Write-Host "Iniciando transferencia de $($sourceFiles.Count) archivo(s)..."
        foreach ($f in $sourceFiles) {{
            $titleFolder.GetFolder.CopyHere($f, 1040)
        }}
        
        $start = Get-Date
        $done = $false
        Write-Host "Copiando... esperando confirmación (máx 5 min)..."
        
        while (((Get-Date) - $start).TotalSeconds -lt 300) {{
            Start-Sleep -Seconds 2
            
            $items = $null
            try {{ $items = $titleFolder.GetFolder.Items() }} catch {{ }}
            
            if ($null -ne $items) {{
                $found = 0
                foreach ($name in $targetNames) {{
                    if ($items | Where-Object {{ $_.Name -eq $name }}) {{ $found++ }}
                }}
                
                if ($found -eq $targetNames.Count) {{
                    $done = $true
                    break
                }}
            }}
        }}
        
        if ($done) {{
            Write-Host "¡Transferencia procesada con éxito!"
            exit 0
        }}
    }} catch {{
        Write-Host "Error Crítico: $($_.Exception.Message)"
        exit 3
    }}
    """
    try:
        process = subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", ps_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        logger.info("[MTP] Iniciando transferencia. Presioná ENTER para saltar la espera si ya ves los archivos.")

        stdout_queue = queue.Queue()
        def reader():
            for line in process.stdout:
                stdout_queue.put(line)

        t = threading.Thread(target=reader, daemon=True)
        t.start()

        success = False
        while True:
            while not stdout_queue.empty():
                line = stdout_queue.get().strip()
                if line:
                    logger.info("[MTP] %s", line)
                    if "exito" in line.lower() or "procesada" in line.lower():
                        success = True
            
            if process.poll() is not None:
                break

            if msvcrt and msvcrt.kbhit():
                key = msvcrt.getch()
                if key in [b'\r', b'\n']: 
                    logger.info("[MTP] Salto manual detectado. Continuando...")
                    try: process.terminate()
                    except: pass
                    success = True
                    break
            
            time.sleep(0.1)
        
        return success or process.returncode == 0
    except Exception as e:
        logger.error("Error ejecutando script MTP: %s", e)
        return False
