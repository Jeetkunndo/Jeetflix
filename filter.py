import requests
import re
import sys
import os

# Palabras clave para buscar
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

# Múltiples fuentes (más chances de encontrar)
FUENTES = [
    "https://iptv-org.github.io/iptv/countries/ar.m3u",
    "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
    "https://m3u.cl/lista/AR"
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
    # Cargar lista actual
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
                        canales_actuales[nombre] = {
                            'extinf': lineas[i],
                            'url': url
                        }
                        i += 2
                    else:
                        i += 1
                else:
                    i += 1
        print(f"📂 Lista actual: {len(canales_actuales)} canales")
    
    # Buscar en todas las fuentes
    todos_los_canales = []
    for fuente in FUENTES:
        contenido = descargar_lista(fuente)
        if contenido:
            todos_los_canales.extend(extraer_canales(contenido))
    
    if not todos_los_canales:
        print("Error: no se pudo descargar ninguna fuente")
        sys.exit(1)
    
    # Buscar canales que coincidan con las palabras clave
    encontrados = {}
    for clave in CANALES:
        print(f"Buscando: {clave}")
        for canal in todos_los_canales:
            if re.search(r'\b' + re.escape(clave) + r'\b', canal['nombre'], re.IGNORECASE):
                if 'youtube.com' in canal['url'] or 'youtu.be' in canal['url']:
                    print(f"  ⚠️ YouTube, ignorado")
                    break
                if verificar_url(canal['url']):
                    encontrados[clave] = canal
                    print(f"  ✅ Encontrado")
                    break
                else:
                    print(f"  ❌ No responde")
                    break
        else:
            print(f"  ❌ No encontrado")
    
    # Combinar: mantener los actuales + agregar los nuevos
    canales_final = {}
    
    # Mantener los que ya andaban
    for nombre, datos in canales_actuales.items():
        if verificar_url(datos['url']):
            canales_final[nombre] = datos
            print(f"  ✓ Manteniendo: {nombre}")
        else:
            print(f"  ✗ Descartando (caído): {nombre}")
    
    # Agregar los nuevos que no estén ya en la lista
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
            print(f"  ➕ Agregando: {canal['nombre']}")
    
    # Guardar lista final
    with open(ARCHIVO_LISTA, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        for nombre, datos in canales_final.items():
            f.write(datos['extinf'] + '\n')
            f.write(datos['url'] + '\n')
    
    print(f"\n✅ Lista final: {len(canales_final)} canales")

if __name__ == "__main__":
    main()
