import json
import math

def distancia(lat1, lon1, lat2, lon2):
    radio = 6371000
    f1 = math.radians(lat1)
    f2 = math.radians(lat2)
    df = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(df / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(dl / 2) ** 2
    return radio * 2 * math.asin(math.sqrt(a))

def adentro(lon, lat, zona):
    return zona["latMin"] <= lat <= zona["latMax"] and zona["lonMin"] <= lon <= zona["lonMax"]

def tramosDeCalle(coords, zona):
    # corta la calle en pedazos que quedan dentro de la zona
    pedazos = {}
    cantidad = 0
    actual = {}
    largo = 0
    for punto in coords:
        if adentro(punto[0], punto[1], zona):
            largo += 1
            actual[largo] = punto
        else:
            if largo >= 2:
                cantidad += 1
                pedazos[cantidad] = actual
            actual = {}
            largo = 0
    if largo >= 2:
        cantidad += 1
        pedazos[cantidad] = actual
    return pedazos

def convertirGeo(archivoEntrada, archivoSalida, zona):
    noAuto = {"footway": True, "path": True, "steps": True, "cycleway": True,
              "pedestrian": True, "track": True, "bridleway": True, "corridor": True}
    with open(archivoEntrada, "r", encoding="utf-8") as f:
        datos = json.load(f)

    # paso 1: juntar los pedazos de calle que sirven para autos
    calles = {}
    cuantas = 0
    veces = {}
    for feature in datos["features"]:
        if feature["geometry"]["type"] != "LineString":
            continue
        props = feature["properties"]
        if props.get("highway") in noAuto:
            continue
        nombre = props.get("name")
        if nombre is None:
            continue
        pedazos = tramosDeCalle(feature["geometry"]["coordinates"], zona)
        for p in pedazos:
            cuantas += 1
            calles[cuantas] = {"nombre": nombre, "mano": props.get("oneway", "no"), "puntos": pedazos[p]}
            for i in pedazos[p]:
                clave = str(pedazos[p][i][1]) + "," + str(pedazos[p][i][0])
                veces[clave] = veces.get(clave, 0) + 1

    # paso 2: quedarse solo con las esquinas (puntos compartidos o extremos)
    nodos = {}
    tramos = {}
    for c in calles:
        puntos = calles[c]["puntos"]
        total = len(puntos)
        mano = calles[c]["mano"]
        anterior = None
        acumulado = 0
        for i in range(1, total + 1):
            lon = puntos[i][0]
            lat = puntos[i][1]
            if i > 1:
                acumulado += distancia(puntos[i - 1][1], puntos[i - 1][0], lat, lon)
            clave = str(lat) + "," + str(lon)
            esEsquina = veces[clave] > 1 or i == 1 or i == total
            if esEsquina:
                if clave not in nodos:
                    nodos[clave] = {"lat": lat, "lon": lon, "calles": {}}
                    tramos[clave] = {}
                nodos[clave]["calles"][calles[c]["nombre"]] = True
                if anterior is not None and anterior != clave:
                    d = round(acumulado, 1)
                    if mano == "-1":
                        tramos[clave][anterior] = d
                    else:
                        tramos[anterior][clave] = d
                        if mano != "yes":
                            tramos[clave][anterior] = d
                anterior = clave
                acumulado = 0

    with open(archivoSalida, "w", encoding="utf-8") as f:
        json.dump({"nodos": nodos, "tramos": tramos}, f, ensure_ascii=False)
    print("Grafo generado:", len(nodos), "nodos")

zona = {"latMin": -27.480, "latMax": -27.425, "lonMin": -59.025, "lonMax": -58.950}
convertirGeo("export.geojson", "calles.json", zona)
