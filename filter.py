import requests
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Tus canales (los mismos que en canales.txt)
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

# Fuentes de listas M3U (orden de prioridad)
FUENTES = [
    "https://iptv-org.github.io/iptv/countries/ar.m3u",
    "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
    "https://raw.githubusercontent.com/josejesusguzman/iptv/main/playlist.m3u",
    "https://m3u.cl/lista/AR"
]

def descargar_lista(url):
    """Descarga una lista M3U desde una URL"""
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.text
    except:
        pass
    return None

def extraer_canales(contenido):
    """Extrae canales de una lista M3U (formato #EXTINF + URL)"""
    canales = []
    lineas = contenido.splitlines()
    i = 0
    while i < len(lineas):
        if lineas[i].startswith('#EXTINF'):
            # Buscar el nombre del canal en la línea #EXTINF
            nombre = lineas[i].split(',')[-1].strip()
            # La URL está en la línea siguiente
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

def verificar_url(url, timeout=5):
    """Verifica si una URL de stream responde (con timeout corto)"""
    try:
        # Hacemos una petición HEAD para ver si responde
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code < 400
    except:
        return False

def buscar_canal_en_fuentes(nombre_buscar):
    """Busca un canal por nombre en todas las fuentes y devuelve el primero que ande"""
    for fuente in FUENTES:
        contenido = descargar_lista(fuente)
        if not contenido:
            continue
        canales = extraer_canales(contenido)
        for canal in canales:
            # Coincidencia parcial (ignora mayúsculas)
            if re.search(re.escape(nombre_buscar.split('(')[0].strip()), canal['nombre'], re.IGNORECASE):
                # Verificar que el enlace ande
                if verificar_url(canal['url']):
                    return canal
    return None

def main():
    # Descargar la lista principal (iptv-org) que es la que más confianza da
    contenido_principal = descargar_lista(FUENTES[0])
    if not contenido_principal:
        print("Error: no se pudo descargar la lista principal")
        sys.exit(1)
    
    canales_principales = extraer_canales(contenido_principal)
    
    # Diccionario para guardar los canales encontrados
    canales_encontrados = {}
    
    # Primero buscar en la lista principal
    for canal in canales_principales:
        for nombre_buscar in CANALES:
            if re.search(re.escape(nombre_buscar.split('(')[0].strip()), canal['nombre'], re.IGNORECASE):
                # Verificar si anda
                if verificar_url(canal['url']):
                    canales_encontrados[nombre_buscar] = canal
                    break
    
    # Para los que no se encontraron o no andan, buscar en otras fuentes
    for nombre_buscar in CANALES:
        if nombre_buscar not in canales_encontrados:
            print(f"Buscando alternativo para: {nombre_buscar}")
            alternativo = buscar_canal_en_fuentes(nombre_buscar)
            if alternativo:
                canales_encontrados[nombre_buscar] = alternativo
                print(f"  ✓ Encontrado: {alternativo['url'][:50]}...")
            else:
                print(f"  ✗ No se encontró alternativo para: {nombre_buscar}")
    
    # Generar el archivo M3U final
    with open('lista_filtrada.m3u', 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        for nombre, canal in canales_encontrados.items():
            f.write(canal['extinf'] + '\n')
            f.write(canal['url'] + '\n')
    
    print(f"\n✅ Lista generada con {len(canales_encontrados)} canales")

if __name__ == "__main__":
    main()
