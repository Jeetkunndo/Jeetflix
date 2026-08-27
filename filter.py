import requests
import sys

# IMPORTANTE: estos nombres tienen que ser copiados EXACTAMENTE de iptv-org
CANALES = [
    "24/7 Canal de Noticias",
    "Canal 26 (1080p)",
    "TN (1080p)",
    "América TV (1080p)",
    "El Nueve (1080p)",
    "El Siete (1080p)",
    "El Trece (1080p)",
    "La Nación + (576p)",
    "Telefe Interior (720p)"
]

FUENTE = "https://iptv-org.github.io/iptv/countries/ar.m3u"

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

def main():
    print("📡 Descargando iptv-org...")
    contenido = descargar_lista(FUENTE)
    if not contenido:
        print("Error")
        sys.exit(1)
    
    canales_fuente = extraer_canales(contenido)
    encontrados = {}
    
    for buscado in CANALES:
        print(f"Buscando: {buscado}")
        for canal in canales_fuente:
            if canal['nombre'] == buscado:
                if 'youtube.com' in canal['url'] or 'youtu.be' in canal['url']:
                    print(f"  ⚠️ YouTube, ignorado")
                    break
                try:
                    response = requests.head(canal['url'], timeout=3, allow_redirects=True)
                    if response.status_code < 400:
                        encontrados[buscado] = canal
                        print(f"  ✅ OK")
                    else:
                        print(f"  ❌ No responde")
                except:
                    print(f"  ❌ Error")
                break
        else:
            print(f"  ❌ No encontrado")
    
    with open('lista_filtrada.m3u', 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        for nombre, canal in encontrados.items():
            f.write(canal['extinf'] + '\n')
            f.write(canal['url'] + '\n')
    
    print(f"\n✅ {len(encontrados)} canales encontrados")

if __name__ == "__main__":
    main()
