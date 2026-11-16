import json
import math
import os

def cargarDatos(archivo):
    try:
        with open(archivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("No se encontró el archivo", archivo)
    except json.JSONDecodeError:
        print("El JSON tiene errores de formato")
    return None

def sinAcentos(texto):
    cambios = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n"}
    resultado = ""
    for letra in texto.lower():
        resultado += cambios.get(letra, letra)
    return resultado

def buscarEsquina(nodos, texto1, texto2):
    t1 = sinAcentos(texto1)
    t2 = sinAcentos(texto2)
    for idNodo in nodos:
        tiene1 = False
        tiene2 = False
        for calle in nodos[idNodo]["calles"]:
            nombre = sinAcentos(calle)
            if t1 in nombre:
                tiene1 = True
            if t2 in nombre:
                tiene2 = True
        if tiene1 and tiene2:
            return idNodo
    return None

def dijkstra(grafo, origen):
    infinito = float("inf")
    distancias = {}
    previos = {}
    visitados = {}
    for nodo in grafo:
        distancias[nodo] = infinito
    distancias[origen] = 0

    while len(visitados) < len(grafo):
        actual = None
        for nodo in distancias:
            if nodo not in visitados:
                if actual is None or distancias[nodo] < distancias[actual]:
                    actual = nodo
        if distancias[actual] == infinito:
            break
        visitados[actual] = True
        for vecino in grafo[actual]:
            nueva = distancias[actual] + grafo[actual][vecino]
            if nueva < distancias[vecino]:
                distancias[vecino] = nueva
                previos[vecino] = actual
    return distancias, previos

def armarRuta(previos, origen, destino):
    pasos = {}
    cantidad = 0
    actual = destino
    while actual is not None:
        cantidad += 1
        pasos[cantidad] = actual
        if actual == origen:
            break
        actual = previos.get(actual)
    return pasos, cantidad

def nombreEsquina(nodos, idNodo):
    return " y ".join(nodos[idNodo]["calles"])

def calleComun(nodos, a, b):
    for calle in nodos[a]["calles"]:
        if calle in nodos[b]["calles"]:
            return calle
    return "sin nombre"

def armarTramos(grafo, nodos, pasos, cantidad):
    # junta los pasos consecutivos que van por la misma calle
    tramos = {}
    cuantos = 0
    for i in range(cantidad, 1, -1):
        a = pasos[i]
        b = pasos[i - 1]
        calle = calleComun(nodos, a, b)
        metros = grafo[a][b]
        if cuantos > 0 and tramos[cuantos]["calle"] == calle:
            tramos[cuantos]["metros"] += metros
            tramos[cuantos]["hasta"] = b
            tramos[cuantos]["nodos"][len(tramos[cuantos]["nodos"]) + 1] = b
        else:
            cuantos += 1
            tramos[cuantos] = {"calle": calle, "metros": metros, "desde": a, "hasta": b,
                               "nodos": {1: a, 2: b}}
    return tramos, cuantos

def callesQueCruza(nodos, tramo):
    cruces = {}
    for k in range(2, len(tramo["nodos"]) + 1):
        for calle in nodos[tramo["nodos"][k]]["calles"]:
            if calle != tramo["calle"]:
                cruces[calle] = True
    return cruces

def mostrarMapa(grafo, nodos, pasos, cantidad):
    try:
        import networkx as nx
        import matplotlib.pyplot as plt
    except ImportError:
        print("Para ver el mapa instalá: pip install networkx matplotlib")
        return

    red = nx.DiGraph()
    posiciones = {}
    for idNodo in nodos:
        posiciones[idNodo] = (nodos[idNodo]["lon"], nodos[idNodo]["lat"])
    dobleMano = []
    unaMano = []
    for origen in grafo:
        for destino in grafo[origen]:
            red.add_edge(origen, destino)
            if origen in grafo[destino]:
                dobleMano.append((origen, destino))
            else:
                unaMano.append((origen, destino))

    tramosRuta = []
    nodosRuta = []
    for i in range(1, cantidad + 1):
        nodosRuta.append(pasos[i])
        if i < cantidad:
            tramosRuta.append((pasos[i + 1], pasos[i]))
    inicio = pasos[cantidad]
    fin = pasos[1]

    from matplotlib.lines import Line2D
    anchoFigura = 14
    altoFigura = 10
    izquierda = 0.01
    derecha = 0.99
    abajo = 0.01
    arriba = 0.80
    plt.figure(num="Rodrigo Nahuel Kirsch - Federico Molina", figsize=(anchoFigura, altoFigura))
    plt.subplots_adjust(left=izquierda, right=derecha, bottom=abajo, top=arriba)
    # forma de la zona de dibujo (alto / ancho), para centrar el mapa
    forma = ((arriba - abajo) * altoFigura) / ((derecha - izquierda) * anchoFigura)
    nx.draw_networkx_edges(red, posiciones, edgelist=dobleMano, edge_color="lightgray",
                           width=0.6, arrows=False)
    nx.draw_networkx_edges(red, posiciones, edgelist=unaMano, edge_color="steelblue",
                           width=0.8, arrows=True, arrowsize=8, node_size=3)
    nx.draw_networkx_nodes(red, posiciones, node_size=3, node_color="gray")
    # orden de capas (zorder): nombres de calles 3, ruta 5, origen y destino 6, carteles 8 y 10
    flechasRuta = nx.draw_networkx_edges(red, posiciones, edgelist=tramosRuta, edge_color="red",
                                         width=2.5, arrows=True, arrowsize=9, node_size=25)
    for flecha in flechasRuta:
        flecha.set_zorder(5)
    puntosRuta = nx.draw_networkx_nodes(red, posiciones, nodelist=nodosRuta, node_size=25,
                                        node_color="red")
    puntosRuta.set_zorder(5)
    puntoInicio = nx.draw_networkx_nodes(red, posiciones, nodelist=[inicio], node_size=120,
                                         node_color="green")
    puntoInicio.set_zorder(6)
    puntoFin = nx.draw_networkx_nodes(red, posiciones, nodelist=[fin], node_size=120,
                                      node_color="blue")
    puntoFin.set_zorder(6)
    plt.suptitle("Actividad Evaluativa 4 Navegador de Rutas", fontsize=20, fontweight="bold", y=0.985)
    referencias = [Line2D([0], [0], color="red", linewidth=3, label="Camino mínimo (rojo)"),
                   Line2D([0], [0], color="steelblue", linewidth=2, marker=">", markersize=6,
                          label="Calles de mano única (azul)"),
                   Line2D([0], [0], color="lightgray", linewidth=2, label="Doble mano (gris)")]
    plt.figlegend(handles=referencias, title="Referencias:", loc="upper center",
                  bbox_to_anchor=(0.5, 0.945), frameon=False, fontsize=12, title_fontsize=13)
    plt.axis("off")
    if posiciones[inicio][1] <= posiciones[fin][1]:
        sentido = {"origen": -16, "destino": 16}
    else:
        sentido = {"origen": 16, "destino": -16}
    for rotulo, idNodo in (("Origen: ", inicio), ("Destino: ", fin)):
        clave = rotulo.split(":")[0].lower()
        desplazamiento = sentido[clave]
        plt.annotate(rotulo + nombreEsquina(nodos, idNodo), xy=posiciones[idNodo],
                     xytext=(0, desplazamiento), textcoords="offset points", ha="center",
                     va="top" if desplazamiento < 0 else "bottom", fontsize=9, fontweight="bold",
                     bbox=dict(facecolor="white", alpha=1, edgecolor="gray"),
                     annotation_clip=False, zorder=10)
    lons = []
    lats = []
    for idNodo in nodosRuta:
        lons.append(posiciones[idNodo][0])
        lats.append(posiciones[idNodo][1])
    margen = 0.006
    xMin = min(lons) - margen
    xMax = max(lons) + margen
    yMin = min(lats) - margen
    yMax = max(lats) + margen
    proporcion = 1 / math.cos(math.radians((yMin + yMax) / 2))
    # ajustar la zona visible a la forma de la ventana para que el mapa quede centrado y sin espacio sobrante
    ancho = xMax - xMin
    alto = (yMax - yMin) * proporcion
    deseado = ancho * forma
    if alto < deseado:
        centro = (yMin + yMax) / 2
        mitad = deseado / proporcion / 2
        yMin = centro - mitad
        yMax = centro + mitad
    else:
        centro = (xMin + xMax) / 2
        mitad = alto / forma / 2
        xMin = centro - mitad
        xMax = centro + mitad
    plt.xlim(xMin, xMax)
    plt.ylim(yMin, yMax)
    plt.gca().set_aspect(proporcion)

    tramos, cuantos = armarTramos(grafo, nodos, pasos, cantidad)
    enRuta = {}
    for t in range(1, cuantos + 1):
        enRuta[tramos[t]["calle"]] = True

    # calles de alrededor: un cartel por calle, girado según su dirección
    porCalle = {}
    for idNodo in nodos:
        x, y = posiciones[idNodo]
        if xMin <= x <= xMax and yMin <= y <= yMax:
            for calle in nodos[idNodo]["calles"]:
                if calle not in enRuta:
                    if calle not in porCalle:
                        porCalle[calle] = {}
                    porCalle[calle][len(porCalle[calle]) + 1] = idNodo
    for calle in porCalle:
        puntos = porCalle[calle]
        if len(puntos) < 2:
            continue
        primero = puntos[1]
        ultimo = puntos[1]
        for k in puntos:
            if posiciones[puntos[k]][0] < posiciones[primero][0]:
                primero = puntos[k]
            if posiciones[puntos[k]][0] > posiciones[ultimo][0]:
                ultimo = puntos[k]
        dx = posiciones[ultimo][0] - posiciones[primero][0]
        dy = posiciones[ultimo][1] - posiciones[primero][1]
        if abs(dx) < 0.0002:
            for k in puntos:
                if posiciones[puntos[k]][1] < posiciones[primero][1]:
                    primero = puntos[k]
                if posiciones[puntos[k]][1] > posiciones[ultimo][1]:
                    ultimo = puntos[k]
            dx = posiciones[ultimo][0] - posiciones[primero][0]
            dy = posiciones[ultimo][1] - posiciones[primero][1]
        angulo = math.degrees(math.atan2(dy * proporcion, dx))
        if angulo > 90:
            angulo -= 180
        if angulo < -90:
            angulo += 180
        mx = (posiciones[primero][0] + posiciones[ultimo][0]) / 2
        my = (posiciones[primero][1] + posiciones[ultimo][1]) / 2
        plt.text(mx, my, calle, fontsize=6, color="dimgray", rotation=angulo,
                 rotation_mode="anchor", ha="center", va="center",
                 bbox=dict(facecolor="white", alpha=0.7, edgecolor="none", pad=0.5))

    # calles de la ruta, en rojo
    for t in range(1, cuantos + 1):
        x1, y1 = posiciones[tramos[t]["desde"]]
        x2, y2 = posiciones[tramos[t]["hasta"]]
        plt.text((x1 + x2) / 2, (y1 + y2) / 2, tramos[t]["calle"], fontsize=7, color="darkred",
                 ha="center", va="center", zorder=8,
                 bbox=dict(facecolor="white", alpha=0.85, edgecolor="none", pad=1))
    carpeta = "ruta"
    os.makedirs(carpeta, exist_ok=True)
    numero = 1
    while os.path.exists(os.path.join(carpeta, "ruta" + str(numero) + ".png")):
        numero += 1
    archivo = os.path.join(carpeta, "ruta" + str(numero) + ".png")
    plt.savefig(archivo, dpi=150)
    print("Imagen guardada en", archivo)
    plt.show()
    plt.close()

def pedirSiNo(pregunta):
    while True:
        respuesta = input(pregunta).strip().lower()
        if respuesta == "s":
            return True
        if respuesta == "n":
            return False
        print("Respondé s o n")

def pedirEsquina(nodos, etiqueta):
    while True:
        print(etiqueta, "(dejá la primera calle vacía para volver al menú)")
        calle1 = input("  Primera calle: ")
        if calle1.strip() == "":
            print("  Cancelado.")
            return None
        calle2 = input("  Segunda calle: ")
        idNodo = buscarEsquina(nodos, calle1, calle2)
        if idNodo is None:
            print("  No encontré esa esquina, probá con otro nombre.")
        else:
            print("  Encontrada:", nombreEsquina(nodos, idNodo))
            return idNodo

def calcularRuta(grafo, nodos):
    origen = pedirEsquina(nodos, "Esquina de origen")
    if origen is None:
        return
    destino = pedirEsquina(nodos, "Esquina de destino")
    if destino is None:
        return
    distancias, previos = dijkstra(grafo, origen)
    if distancias[destino] == float("inf"):
        print("No hay camino entre esas esquinas")
        return

    pasos, cantidad = armarRuta(previos, origen, destino)
    print("Recorrido:")
    ultimo = ""
    for i in range(cantidad, 0, -1):
        esquina = nombreEsquina(nodos, pasos[i])
        if esquina != ultimo:
            print(" ->", esquina)
        ultimo = esquina
    print("Distancia total:", round(distancias[destino]), "metros")

    tramos, cuantos = armarTramos(grafo, nodos, pasos, cantidad)
    print("Calles del recorrido:")
    acumulado = 0
    for t in range(1, cuantos + 1):
        acumulado += tramos[t]["metros"]
        print(" ", t, "-", tramos[t]["calle"], ":", round(tramos[t]["metros"]),
              "m (acumulado", round(acumulado), "m )")
        cruces = callesQueCruza(nodos, tramos[t])
        if len(cruces) > 0:
            print("      cruza con:", ", ".join(cruces))

    mostrarMapa(grafo, nodos, pasos, cantidad)

def eliminarArista(grafo, nodos):
    idNodo = pedirEsquina(nodos, "Esquina donde empieza el tramo a eliminar")
    if idNodo is None:
        return
    vecinos = grafo[idNodo]
    if len(vecinos) == 0:
        print("Desde esa esquina no sale ningún tramo.")
        return

    numeradas = {}
    numero = 0
    print("Tramos que salen de", nombreEsquina(nodos, idNodo) + ":")
    for destino in vecinos:
        numero += 1
        numeradas[numero] = destino
        print(" ", numero, "-", calleComun(nodos, idNodo, destino), "hasta",
              nombreEsquina(nodos, destino), "(", round(vecinos[destino]), "m )")

    try:
        elegido = int(input("Número del tramo a eliminar: "))
    except ValueError:
        print("Tenés que escribir un número.")
        return
    if elegido not in numeradas:
        print("Número inválido.")
        return

    destino = numeradas[elegido]
    del grafo[idNodo][destino]
    print("Tramo eliminado.")
    if idNodo in grafo[destino]:
        if pedirSiNo("Esa calle también es de doble mano. ¿Eliminar también el sentido contrario? (s/n): "):
            del grafo[destino][idNodo]
            print("Sentido contrario eliminado.")

def eliminarNodo(grafo, nodos):
    idNodo = pedirEsquina(nodos, "Esquina a eliminar")
    if idNodo is None:
        return
    if not pedirSiNo("¿Eliminar " + nombreEsquina(nodos, idNodo) + " y todos sus tramos? (s/n): "):
        print("No se eliminó nada.")
        return
    for origen in grafo:
        if idNodo in grafo[origen]:
            del grafo[origen][idNodo]
    del grafo[idNodo]
    del nodos[idNodo]
    print("Esquina eliminada.")

def mostrarMenu():
    print()
    print("<===== NAVEGADOR DE RUTAS - RESISTENCIA =====>")
    print("1 - Calcular ruta")
    print("2 - Eliminar una arista (tramo de calle)")
    print("3 - Eliminar un nodo (esquina)")
    print("4 - Salir")

def main():
    datos = cargarDatos("calles.json")
    if datos is None:
        return
    nodos = datos["nodos"]
    grafo = datos["tramos"]

    opcion = ""
    while opcion != "4":
        mostrarMenu()
        opcion = input("Elegí una opción: ").strip()
        match opcion:
            case "1":
                calcularRuta(grafo, nodos)
            case "2":
                eliminarArista(grafo, nodos)
            case "3":
                eliminarNodo(grafo, nodos)
            case "4":
                print("Hasta luego")
            case _:
                print("Opción inválida, elegí del 1 al 4.")

main()
