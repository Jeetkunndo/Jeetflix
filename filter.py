import requests
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Tus canales
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

# Múltiples fuentes (orden de prioridad)
FUENTES = [
    "https://iptv-org.github.io/iptv/countries/ar.m3u",
    "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
    "https://raw.githubusercontent.com/josejesusguzman/iptv/main/playlist.m3u",
    "https://m3u.cl/lista/AR"
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
            partes = lineas[i].split(',')
            nombre = partes[-1].strip() if len(partes) > 1 else ""
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
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code < 400
    except:
        return False

def buscar_canal_en_todas_fuentes(nombre_buscar):
    for fuente in FUENTES:
        contenido = descargar_lista(fuente)
        if not contenido:
            continue
        canales = extraer_canales(contenido)
        for canal in canales:
            if canal['nombre'] == nombre_buscar:
                if verificar_url(canal['url']):
                    return canal
    return None

def main():
    canales_encontrados = {}
    for nombre_buscar in CANALES:
        print(f"Buscando: {nombre_buscar}")
        canal = buscar_canal_en_todas_fuentes(nombre_buscar)
        if canal:
            canales_encontrados[nombre_buscar] = canal
            print(f"  ✓ Encontrado")
        else:
            print(f"  ✗ No encontrado")
    
    with open('lista_filtrada.m3u', 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        for nombre, canal in canales_encontrados.items():
            f.write(canal['extinf'] + '\n')
            f.write(canal['url'] + '\n')
    
    print(f"\n✅ Lista generada con {len(canales_encontrados)} canales")

if __name__ == "__main__":
    main()
