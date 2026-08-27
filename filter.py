import requests
import re
import unicodedata
import sys

# Tus canales (sin A24 porque da error y sin resoluciones para que coincidan mejor)
CANALES = [
    "24/7 Canal de Noticias",
    "Canal 26",
    "TN",
    "America TV",
    "El Nueve",
    "El Siete",
    "El Trece",
    "La Nacion +",
    "Telefe Interior"
]

# Fuentes
FUENTES = [
    "https://iptv-org.github.io/iptv/countries/ar.m3u",
    "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
    "https://m3u.cl/lista/AR"
]

def limpiar(texto):
    # Quita paréntesis y su contenido
    texto = re.sub(r'\s*\([^)]*\)\s*', ' ', texto)
    # Quita símbolos como +, -, etc.
    texto = re.sub(r'[^\w\s]', ' ', texto)
    # Quita tildes
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    # Minúsculas y espacios extra
    texto = ' '.join(texto.lower().split())
    return texto

def descargar_lista(url):
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.text
    except:
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
                    'nombre_original': nombre,
                    'nombre_limpio': limpiar(nombre),
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

def main():
    # Limpiar nombres de tus canales
    canales_a_buscar = {limpiar(c): c for c in CANALES}
    canales_encontrados = {}
    
    for fuente in FUENTES:
        contenido = descargar_lista(fuente)
        if not contenido:
            continue
        canales_fuente = extraer_canales(contenido)
        
        for clave, nombre_original in canales_a_buscar.items():
            if nombre_original in canales_encontrados:
                continue
            for canal in canales_fuente:
                # Coincidencia exacta después de limpiar
                if canal['nombre_limpio'] == clave:
                    # Excluir YouTube (no funciona en Jellyfin)
                    if 'youtube.com' in canal['url'] or 'youtu.be' in canal['url']:
                        print(f"⚠️ {nombre_original} es YouTube, ignorado")
                        break
                    if verificar_url(canal['url']):
                        canales_encontrados[nombre_original] = canal
                        print(f"✓ {nombre_original}")
                        break
    
    with open('lista_filtrada.m3u', 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        for nombre, canal in canales_encontrados.items():
            f.write(canal['extinf'] + '\n')
            f.write(canal['url'] + '\n')
    
    print(f"\n✅ Lista generada con {len(canales_encontrados)} canales")

if __name__ == "__main__":
    main()
