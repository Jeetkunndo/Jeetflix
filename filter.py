import requests
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Tus canales (coincidencia EXACTA)
CANALES = [
    "24/7 Canal de Noticias",
    "A24 (720p)",
    "Canal 26 (1080p)",
    "TN (1080p)",
    "America TV (1080p)",
    "El Nueve (1080p)",
    "El Siete (1080p)",
    "El Trece (1080p)",
    "La Nacion + (576p)",
    "Telefe Interior (720p)"
]

# Fuentes (solo iptv-org, la más confiable para nombres exactos)
FUENTES = [
    "https://iptv-org.github.io/iptv/countries/ar.m3u"
]

def descargar_lista(url):
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.text
    except:
        pass
    return None

def extraer_canales(contenido):
    canales = []
    lineas = contenido.splitlines()
    i = 0
    while i < len(lineas):
        if lineas[i].startswith('#EXTINF'):
            # Buscar el nombre del canal después de la última coma
            partes = lineas[i].split(',')
            if len(partes) > 1:
                nombre = partes[-1].strip()
            else:
                nombre = ""
            if i + 1 < len(lineas) and not lineas[i+1].startswith('#'):
                url = lineas[i+1].strip()
                canales.append({
                    'nombre': nombre,
                    'extinf': lineas[i],
                    'url': url
                })
                i += 2
            else:
                i += 1
        else:
            i += 1
    return canales

def verificar_url(url, timeout=3):
    """Verifica si una URL responde (timeout más corto)"""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code < 400
    except:
        return False

def main():
    contenido_principal = descargar_lista(FUENTES[0])
    if not contenido_principal:
        print("Error: no se pudo descargar la lista")
        sys.exit(1)
    
    canales_principales = extraer_canales(contenido_principal)
    
    # Buscar coincidencia EXACTA
    canales_encontrados = {}
    for nombre_buscar in CANALES:
        for canal in canales_principales:
            if canal['nombre'] == nombre_buscar:  # COINCIDENCIA EXACTA
                if verificar_url(canal['url']):
                    canales_encontrados[nombre_buscar] = canal
                    print(f"✓ {nombre_buscar}: OK")
                else:
                    print(f"✗ {nombre_buscar}: enlace muerto")
                break
        else:
            print(f"✗ {nombre_buscar}: no encontrado en la fuente")
    
    # Generar archivo M3U final
    with open('lista_filtrada.m3u', 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        for nombre, canal in canales_encontrados.items():
            f.write(canal['extinf'] + '\n')
            f.write(canal['url'] + '\n')
    
    print(f"\n✅ Lista generada con {len(canales_encontrados)} canales")

if __name__ == "__main__":
    main()
