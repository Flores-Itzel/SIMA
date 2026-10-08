import math
# Constantes (umbrales de simulacion - Tabla 3 del proyecto)
TEMP_MAX = 30       # Alerta si temperatura > 30 C
HUM_MIN = 30        # Alerta si humedad < 30 %
HUM_MAX = 70        # Alerta si humedad > 70 %
CO2_MAX = 1000      # Alerta si CO2 > 1000 ppm

ANCHO = 60          # Ancho de los separadores de consola

# Clases
class Medicion:
    """Representa una medicion ambiental de un espacio."""

    def __init__(self, id, espacio, temperatura, humedad, co2):
        self.id = id
        self.espacio = espacio
        self.temperatura = temperatura
        self.humedad = humedad
        self.co2 = co2

    def mostrar(self):
        print(f"ID: {self.id}")
        print(f"Espacio: {self.espacio}")
        print(f"Temperatura: {self.temperatura} °C")
        print(f"Humedad: {self.humedad} %")
        print(f"CO2: {self.co2} ppm")


class Alerta:
    """Representa una alerta generada por una condicion fuera de umbral.

    id_medicion es opcional: permite saber que medicion origino la alerta
    y asi retirarla de la cola si ese registro se deshace.
    """

    def __init__(self, id, espacio, variable, valor, descripcion,
                 id_medicion=None):
        self.id = id
        self.espacio = espacio
        self.variable = variable
        self.valor = valor
        self.descripcion = descripcion
        self.estado = "Pendiente"
        self.id_medicion = id_medicion

    def mostrar(self):
        print(f"ID de alerta: {self.id}")
        print(f"Espacio: {self.espacio}")
        print(f"Variable: {self.variable}")
        print(f"Valor registrado: {self.valor}")
        print(f"Descripción: {self.descripcion}")
        print(f"Estado: {self.estado}")

    def atender(self):
        self.estado = "Atendida"

# Estado del sistema: las tres estructuras de datos y los contadores
mediciones = []          # LISTA de objetos Medicion
alertas = []             # COLA de objetos Alerta (FIFO)
deshacer = []            # PILA con el ID de cada medicion registrada (LIFO)

siguiente_id_medicion = 1
siguiente_id_alerta = 1
alertas_atendidas = 0


def reiniciar_sistema():
    """Deja las tres estructuras y los contadores en su estado inicial."""
    global siguiente_id_medicion, siguiente_id_alerta, alertas_atendidas
    mediciones.clear()
    alertas.clear()
    deshacer.clear()
    siguiente_id_medicion = 1
    siguiente_id_alerta = 1
    alertas_atendidas = 0

# Utilerias de consola
def titulo(texto):
    print()
    print("=" * ANCHO)
    print(texto.center(ANCHO))
    print("=" * ANCHO)


def separador():
    print("-" * ANCHO)


def leer_numero(mensaje, minimo, maximo):
    """Pide un numero y lo valida. Regresa float o None si es invalido."""
    texto = input(mensaje).strip()
    try:
        valor = float(texto)
    except ValueError:
        print(f"  [ERROR] '{texto}' no es un número válido.")
        return None
    if not math.isfinite(valor):          # rechaza 'nan' e 'inf'
        print(f"  [ERROR] '{texto}' no es un número válido.")
        return None
    if valor < minimo or valor > maximo:
        print(f"  [ERROR] El valor debe estar entre {minimo} y {maximo}.")
        return None
    return valor


def pedir_espacio():
    """Selecciona el espacio por numero. Regresa el nombre o None."""
    print("Espacios disponibles:")
    print("  1. Aula")
    print("  2. Laboratorio")
    print("  3. Biblioteca")
    opcion = input("Seleccione el espacio (1-3): ").strip()
    if opcion == "1":
        numero = input("Número de aula (Enter para omitir): ").strip()
        if numero == "":
            return "Aula"
        if not numero.isdigit():
            print("  [ERROR] El número de aula debe ser entero.")
            return None
        return f"Aula {numero}"
    if opcion == "2":
        return "Laboratorio"
    if opcion == "3":
        return "Biblioteca"
    print("  [ERROR] Espacio no válido. Elija 1, 2 o 3.")
    return None

# Logica del sistema (sin entrada de usuario, facil de probar)
def generar_alertas(medicion):
    """Revisa los 3 umbrales y ENCOLA una alerta por cada condicion.

    Regresa cuantas alertas se generaron.
    """
    global siguiente_id_alerta
    generadas = 0

    if medicion.temperatura > TEMP_MAX:
        alertas.append(Alerta(siguiente_id_alerta, medicion.espacio,
                              "Temperatura", medicion.temperatura,
                              "Temperatura elevada", medicion.id))
        siguiente_id_alerta += 1
        generadas += 1

    if medicion.humedad < HUM_MIN or medicion.humedad > HUM_MAX:
        if medicion.humedad < HUM_MIN:
            texto = "Humedad baja (ambiente seco)"
        else:
            texto = "Humedad alta (ambiente húmedo)"
        alertas.append(Alerta(siguiente_id_alerta, medicion.espacio,
                              "Humedad", medicion.humedad, texto,
                              medicion.id))
        siguiente_id_alerta += 1
        generadas += 1

    if medicion.co2 > CO2_MAX:
        alertas.append(Alerta(siguiente_id_alerta, medicion.espacio,
                              "CO2", medicion.co2, "CO2 elevado",
                              medicion.id))
        siguiente_id_alerta += 1
        generadas += 1

    return generadas


def crear_medicion(espacio, temperatura, humedad, co2):
    """Crea la medicion, la guarda en la LISTA, apila su ID en la PILA y
    genera sus alertas en la COLA. Regresa (medicion, num_alertas)."""
    global siguiente_id_medicion
    m = Medicion(siguiente_id_medicion, espacio, temperatura, humedad, co2)
    siguiente_id_medicion += 1
    mediciones.append(m)          # LISTA
    deshacer.append(m.id)         # PILA
    return m, generar_alertas(m)  # COLA


def retirar_alerta():
    """Retira de la COLA la primera alerta (FIFO) y la marca como atendida.
    Regresa la alerta o None si la cola esta vacia."""
    global alertas_atendidas
    if len(alertas) == 0:
        return None
    a = alertas.pop(0)
    a.atender()
    alertas_atendidas += 1
    return a


def revertir_registro():
    """Saca el ultimo ID de la PILA y elimina esa medicion de la LISTA.
    Tambien retira de la COLA las alertas pendientes que habia generado.
    Regresa (medicion, alertas_retiradas) o None si la pila esta vacia."""
    if len(deshacer) == 0:
        return None
    id_buscado = deshacer.pop()                    # PILA: LIFO

    eliminada = None
    for i in range(len(mediciones)):               # busca por ID en la lista
        if mediciones[i].id == id_buscado:
            eliminada = mediciones.pop(i)
            break

    # Conserva en la cola solo las alertas que NO vienen de esa medicion
    restantes = []
    retiradas = 0
    for a in alertas:
        if a.id_medicion == id_buscado:
            retiradas += 1
        else:
            restantes.append(a)
    alertas.clear()
    for a in restantes:
        alertas.append(a)

    return eliminada, retiradas


def calcular_estadisticas():
    """Calcula con ciclos las estadisticas de la Tabla 5.

    Regresa (total, prom_temp, max_temp, min_temp, prom_hum, prom_co2).
    Si no hay mediciones, los valores numericos son None (evita dividir
    entre cero)."""
    total = 0
    suma_temp = 0.0
    suma_hum = 0.0
    suma_co2 = 0.0
    max_temp = None
    min_temp = None

    for m in mediciones:
        total += 1
        suma_temp += m.temperatura
        suma_hum += m.humedad
        suma_co2 += m.co2
        if max_temp is None or m.temperatura > max_temp:
            max_temp = m.temperatura
        if min_temp is None or m.temperatura < min_temp:
            min_temp = m.temperatura

    if total == 0:
        return 0, None, None, None, None, None
    return (total, suma_temp / total, max_temp, min_temp,
            suma_hum / total, suma_co2 / total)

# Funciones del menu (interaccion con el usuario)
def registrar_medicion():
    titulo("REGISTRAR MEDICIÓN")
    espacio = pedir_espacio()
    if espacio is None:
        print("Registro cancelado.")
        return
    temperatura = leer_numero("Temperatura (°C) [-50 a 100]: ", -50, 100)
    if temperatura is None:
        print("Registro cancelado.")
        return
    humedad = leer_numero("Humedad relativa (%) [0 a 100]: ", 0, 100)
    if humedad is None:
        print("Registro cancelado.")
        return
    co2 = leer_numero("CO2 (ppm) [0 a 10000]: ", 0, 10000)
    if co2 is None:
        print("Registro cancelado.")
        return

    m, n_alertas = crear_medicion(espacio, temperatura, humedad, co2)
    separador()
    print(f"Medición #{m.id} registrada correctamente en '{m.espacio}'.")
    if n_alertas == 0:
        print("Sin alertas: todas las variables están dentro de los umbrales.")
    else:
        print(f"Se generaron {n_alertas} alerta(s) y se agregaron a la cola.")


def consultar_mediciones():
    titulo("MEDICIONES REGISTRADAS")
    if len(mediciones) == 0:
        print("No hay mediciones registradas todavía.")
        return
    for m in mediciones:
        m.mostrar()
        separador()
    print(f"Total de mediciones: {len(mediciones)}")


def consultar_alertas():
    titulo("ALERTAS PENDIENTES (orden de atención)")
    if len(alertas) == 0:
        print("No hay alertas pendientes.")
        return
    posicion = 1
    for a in alertas:
        print(f"[Posición {posicion} en la cola]")
        a.mostrar()
        separador()
        posicion += 1
    print(f"Alertas pendientes: {len(alertas)}")


def atender_alerta():
    titulo("ATENDER ALERTA")
    if len(alertas) == 0:
        print("No hay alertas pendientes por atender.")
        return
    print("Siguiente alerta en la cola:")
    separador()
    alertas[0].mostrar()
    separador()
    respuesta = input("¿Marcar como atendida? (s/n): ").strip().lower()
    if respuesta == "s":
        a = retirar_alerta()
        print(f"Alerta #{a.id} atendida y retirada de la cola.")
        print(f"Alertas pendientes restantes: {len(alertas)}")
    else:
        print("La alerta sigue pendiente en la cola.")


def deshacer_registro():
    titulo("DESHACER ÚLTIMO REGISTRO")
    if len(deshacer) == 0:
        print("No hay registros que deshacer.")
        return
    resultado = revertir_registro()
    m, retiradas = resultado
    print(f"Operación revertida: se eliminó la medición #{m.id} "
          f"({m.espacio}).")
    if retiradas > 0:
        print(f"También se retiraron {retiradas} alerta(s) pendiente(s) "
              f"de esa medición.")


def mostrar_estadisticas():
    titulo("ESTADÍSTICAS AMBIENTALES")
    total, prom, mx, mn, prom_h, prom_c = calcular_estadisticas()
    print(f"Total de mediciones   : {total}")
    if total == 0:
        print("Temperatura promedio  : sin datos")
        print("Temperatura máxima    : sin datos")
        print("Temperatura mínima    : sin datos")
        print("Humedad promedio      : sin datos")
        print("CO2 promedio          : sin datos")
    else:
        print(f"Temperatura promedio  : {prom:.2f} °C")
        print(f"Temperatura máxima    : {mx} °C")
        print(f"Temperatura mínima    : {mn} °C")
        print(f"Humedad promedio      : {prom_h:.2f} %")
        print(f"CO2 promedio          : {prom_c:.2f} ppm")
    separador()
    print(f"Alertas pendientes    : {len(alertas)}")
    print(f"Alertas atendidas     : {alertas_atendidas}")

# Menu principal
def mostrar_menu():
    titulo("SIMA - MONITOREO AMBIENTAL")
    print("  1. Registrar medición")
    print("  2. Consultar mediciones")
    print("  3. Consultar alertas pendientes")
    print("  4. Atender alerta")
    print("  5. Deshacer último registro")
    print("  6. Mostrar estadísticas")
    print("  7. Salir")
    separador()


def ejecutar_opcion(opcion):
    """Ejecuta la opcion elegida. Regresa False si el usuario quiere salir."""
    if opcion == "1":
        registrar_medicion()
    elif opcion == "2":
        consultar_mediciones()
    elif opcion == "3":
        consultar_alertas()
    elif opcion == "4":
        atender_alerta()
    elif opcion == "5":
        deshacer_registro()
    elif opcion == "6":
        mostrar_estadisticas()
    elif opcion == "7":
        print("\nGracias por usar SIMA. ¡Hasta pronto!")
        return False
    else:
        print("  [ERROR] Opción no válida. Elija un número del 1 al 7.")
    return True


def menu_principal():
    continuar = True
    while continuar:
        mostrar_menu()
        try:
            opcion = input("Seleccione una opción: ").strip()
        except EOFError:          # fin de la entrada: salir sin error
            break
        continuar = ejecutar_opcion(opcion)
        if continuar:
            try:
                input("\nPresione Enter para volver al menú...")
            except EOFError:
                break


if __name__ == "__main__":
    menu_principal()