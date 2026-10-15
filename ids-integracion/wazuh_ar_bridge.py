"""
Puente Active-Response Wazuh -> IDS webhook
===========================================

Este script lo EJECUTA el agente de Wazuh en DC01 cuando el manager (en AWS)
detecta un brute-force y ordena un active-response.

Protocolo de active-response de Wazuh (4.x):
  - El agente ejecuta este script y le pasa la alerta como JSON por STDIN.
  - El JSON trae, entre otras cosas, el comando ("add" = actuar) y los datos
    del evento, incluida la IP origen del atacante.

Su unico trabajo (puente delgado): leer ese JSON -> sacar la IP -> hacer POST
al webhook local (127.0.0.1:5000/block). Toda la logica de decision
(allowlist, bloqueo, expiracion) vive en el webhook, no aqui.
"""

import sys
import json
import urllib.request

WEBHOOK_URL = "http://127.0.0.1:5000/block"

# Archivo de log propio del puente (para depurar el active-response)
LOG_PATH = r"C:\ids\ar_bridge.log"


def log(msg: str) -> None:
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass  # el logging nunca debe tumbar el active-response


def extract_ip(alert: dict) -> str | None:
    """Saca la IP origen del atacante de la alerta de Wazuh.
    En eventos 4625 de Windows (eventchannel) la IP vive anidada; probamos
    varias rutas conocidas por robustez."""
    data = alert.get("data", {})

    # Ruta 1: campo normalizado por el decoder de Wazuh
    if data.get("srcip"):
        return data["srcip"]

    # Ruta 2: eventdata de Windows (lo mas comun para 4625 via eventchannel)
    ip = data.get("win", {}).get("eventdata", {}).get("ipAddress")
    if ip:
        return ip

    return None


def main() -> None:
    raw = sys.stdin.readline()
    if not raw:
        log("Sin input en stdin; nada que hacer")
        return

    try:
        message = json.loads(raw)
    except json.JSONDecodeError as e:
        log(f"JSON invalido en stdin: {e}")
        return

    command = message.get("command")
    if command != "add":
        log(f"Comando '{command}' ignorado (solo actuamos en 'add')")
        return

    alert = message.get("parameters", {}).get("alert", {})
    ip = extract_ip(alert)
    if not ip:
        log("No se pudo extraer la IP de la alerta")
        return

    # POST al webhook local
    payload = json.dumps({"ip": ip}).encode("utf-8")
    req = urllib.request.Request(
        WEBHOOK_URL, data=payload,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode(errors="ignore")
            log(f"IP {ip} -> webhook respondio: {body}")
    except Exception as e:
        log(f"Error al llamar al webhook para {ip}: {e}")


if __name__ == "__main__":
    main()
