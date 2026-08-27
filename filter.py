import requests
import re
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Palabras clave para buscar tus canales
CANALES = [
    "24/7 Canal de Noticias",
    "Canal 26",
    "TN",
    "América TV",
    "El Nueve",
    "El Siete",
    "El Trece",
    "La Nación +",
    "Telefe Interior"
]

# Múltiples fuentes (ampliado a 15)
FUENTES = [
    "https://iptv-org.github.io/iptv/countries/ar.m3u",
    "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
    "https://m3u.cl/lista/AR",
    "https://raw.githubusercontent.com/josejesusguzman/iptv/main/playlist.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/countries/ar.m3u",
    "https://raw.githubusercontent.com/twz915/IPTV/main/IPTV-Argentina.m3u",
    "https://raw.githubusercontent.com/matiaspe/IPTV/main/listado.m3u",
    "https://raw.githubusercontent.com/andrew2022/iptv/master/playlist.m3u",
    "https://raw.githubusercontent.com/MiguelAngel2201/IPTV/main/Argentina.m3u",
    "https://raw.githubusercontent.com/gnfisher/IPTV/main/playlist.m3u",
    "https://raw.githubusercontent.com/IPTVCAT/IPTV/main/playlist.m3u",
    "https://raw.githubusercontent.com/PedroGonzalez/IPTV/main/list.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/sat/ar.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/radio/countries/ar.m3u",
    "https://raw.githubusercontent.com/EddieLuis/IPTV/main/playlist.m3u"
]

ARCHIVO_LISTA = "lista_filtrada.m3u"

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

def verificar_url(url):
    try:
        response = requests.head(url, timeout=3, allow_redirects=True)
        return response.status_code < 400
    except:
        return False

def main():
    # Leer lista actual
    canales_actuales = {}
    if os.path.exists(ARCHIVO_LISTA):
        with open(ARCHIVO_LISTA, 'r', encoding='utf-8') as f:
            contenido = f.read()
            lineas = contenido.splitlines()
            i = 0
            while i < len(lineas):
                if lineas[i].startswith('#EXTINF'):
                    partes = lineas[i].split(',')
                    nombre = partes[-1].strip() if len(partes) > 1 else ""
                    if i + 1 < len(lineas) and not lineas[i+1].startswith('#'):
                        url = lineas[i+1].strip()
                        if verificar_url(url):
                            canales_actuales[nombre] = {
                                'extinf': lineas[i],
                                'url': url
                            }
                        i += 2
                    else:
                        i += 1
                else:
                    i += 1
        print(f"📂 Canales actuales que andan: {len(canales_actuales)}")
    
    # Descargar todas las fuentes en paralelo
    print("📡 Descargando fuentes...")
    contenidos = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futuros = {executor.submit(descargar_lista, url): url for url in FUENTES}
        for futuro in as_completed(futuros):
            resultado = futuro.result()
            if resultado:
                contenidos.append(resultado)
    
    if not contenidos:
        print("Error: no se pudo descargar ninguna fuente")
        sys.exit(1)
    
    # Extraer canales de todas las fuentes
    todos_los_canales = []
    for contenido in contenidos:
        todos_los_canales.extend(extraer_canales(contenido))
    
    print(f"📡 Total de canales encontrados: {len(todos_los_canales)}")
    
    # Buscar coincidencias
    encontrados = {}
    for clave in CANALES:
        print(f"🔍 Buscando: {clave}")
        for canal in todos_los_canales:
            if re.search(r'\b' + re.escape(clave) + r'\b', canal['nombre'], re.IGNORECASE):
                if 'youtube.com' in canal['url'] or 'youtu.be' in canal['url']:
                    print(f"  ⚠️ YouTube, ignorado")
                    break
                if verificar_url(canal['url']):
                    encontrados[clave] = canal
                    print(f"  ✅ Encontrado: {canal['nombre']}")
                    break
                else:
                    print(f"  ❌ No responde")
                    break
        else:
            print(f"  ❌ No encontrado")
    
    # Combinar listas
    canales_final = dict(canales_actuales)
    for clave, canal in encontrados.items():
        existe = False
        for nombre in canales_final.keys():
            if clave.lower() in nombre.lower() or nombre.lower() in clave.lower():
                existe = True
                break
        if not existe:
            canales_final[canal['nombre']] = {
                'extinf': canal['extinf'],
                'url': canal['url']
            }
            print(f"  ➕ Agregando nuevo: {canal['nombre']}")
    
    # Guardar lista
    with open(ARCHIVO_LISTA, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        for nombre, datos in canales_final.items():
            f.write(datos['extinf'] + '\n')
            f.write(datos['url'] + '\n')
    
    print(f"\n✅ Lista final: {len(canales_final)} canales")

if __name__ == "__main__":
    main()
