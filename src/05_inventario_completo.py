import csv
import json
import requests
from tabulate import tabulate

BASE_URL = "http://localhost:58000/api/v1"
USUARIO = "TU_USUARIO"
PASSWORD = "TU_PASSWORD"

def obtener_ticket():
    headers = {"Content-Type": "application/json"}
    data = json.dumps({"username":"cisco", "password":"class"})
    resp = requests.post(f"{BASE_URL}/ticket", data=data, headers=headers)
    if resp.status_code == 201:
        return resp.json()["response"]["serviceTicket"]
    raise Exception(f"Error de autenticación ({resp.status_code}): {resp.text}")

def main():
    ticket = obtener_ticket()
    headers = {"X-Auth-Token": ticket, "Content-Type": "application/json"}

    # 1. Consultar dispositivos de red (/network-device) y hosts (/host)
    dispositivos = requests.get(f"{BASE_URL}/network-device", headers=headers).json().get("response", [])
    hosts = requests.get(f"{BASE_URL}/host", headers=headers).json().get("response", [])

    # 2. Construir inventario unificado con métricas y detalles de red
    inventario = []
    encabezados = ["Categoría", "Hostname", "IP", "MAC", "Estado / Puerto", "ID (UUID)"]
    alcanzables = 0

    for eq in dispositivos:
        estado = eq.get("reachabilityStatus", "N/A")
        if estado == "Reachable":
            alcanzables += 1
        inventario.append([
            "Infraestructura",
            eq.get("hostname", "N/A"),
            eq.get("managementIpAddress", "N/A"),
            eq.get("macAddress", "N/A"),
            f"{estado} ({eq.get('inventoryStatusDetail', 'N/A')})",
            eq.get("id", "N/A")
        ])

    for h in hosts:
        inventario.append([
            "Host Final",
            h.get("hostName", "Host"),
            h.get("hostIp", "N/A"),
            h.get("hostMac", "N/A"),
            f"Conectado a {h.get('connectedInterfaceName', 'N/A')}",
            h.get("id", "N/A")
        ])

    # 3. Mostrar tabla consolidada y resumen de salud de la red
    print("\n=== INVENTARIO CONSOLIDADO DE RED ===")
    print(tabulate(inventario, headers=encabezados, tablefmt="grid"))
    print(f"\nResumen: {len(dispositivos)} equipos de red ({alcanzables} Reachable) | {len(hosts)} hosts finales.")

    # 4. Exportar inventario a archivo CSV
    archivo_csv = "inventario_red.csv"
    with open(archivo_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(encabezados)
        writer.writerows(inventario)
    print(f"[OK] Reporte exportado a '{archivo_csv}'.")

    # 5. Gestión activa: permitir eliminar un dispositivo de red por ID (DELETE)
    id_borrar = input("\nIngresa el ID (UUID) de un equipo de red para eliminarlo (o Enter para finalizar): ").strip()
    if id_borrar:
        resp_del = requests.delete(f"{BASE_URL}/network-device/{id_borrar}", headers=headers)
        print(f"Respuesta DELETE (Status {resp_del.status_code}):", resp_del.json())

if __name__ == "__main__":
    main()