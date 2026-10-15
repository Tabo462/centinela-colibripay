from flask import Flask, request, jsonify
import subprocess
import threading
import logging
import ipaddress
from datetime import datetime


# ====================== Configuracion ==============================

BLOCK_DURATION_MINUTES = 30 # El bloque dura 30 minutos
LISTEN_PORT = 5000 # El puerto donde escucha el webhook


# Allowlist: IPs que NUNCA se bloquean para prevenir Auto-DoS

ALLOWLIST = {
    "127.0.0.1", #Localhost
    "::1",       #Localhost IPv6
    "10.0.2.10", #DC01 - El propio controlador de dominio
    "10.0.2.1", # Gateway de la red del lab
}


app = Flask(__name__)


# ====Endpoint que recibe la orden de bloque desde Wazuh====
@app.route("/block", methods=["POST"])
def block_endpoint():
    data = request.get_json(silent = True)

    # 1. Validamos que llego un JSON con el campo 'ip'
    if not data or "ip" not in data:
        log.warning("Peticion inválida: falta el campo 'ip'")
        return jsonify({"status": "error", "reason": "missing 'ip' field"}), 400

    ip = data["ip"].strip()

    # 2. Validamos que sea una IP real
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        log.warning("IP invalida recibida: %s", ip)
        return jsonify({"status": "error", "reason": "invalid IP"}), 400


    # 3. Pasar a la logica de decision
    result = handle_block_request(ip)
    return jsonify(result), 200


# === Estado IPs bloqueadas actualmente ===
blocked_ips: dict[str, datetime] = {}
_lock = threading.Lock() # Protege blocked_ips de accesos simultaneos

# === Logica de decision ===

def handle_block_request(ip: str) -> dict:

    # Restriccion 1: Allowlist

    if ip in ALLOWLIST:
        log.warning("ALERTA: actividad sospechosa desde IP protegida %s "
                    "(allowlist) — NO se bloquea, requiere revisión humana", ip)

        return {"status": "allowlisted", "ip": ip,
                "action": "none", "note": "IP protegida — alertada, no bloqueada"}

    with _lock:

        if ip in blocked_ips:
            log.info("IP %s ya estaba bloqueada; sin accion", ip)
            return {"status": "already_blocked", "ip": ip, "action": "none"}

        ok = block_ip(ip)
        if not ok:
             return {"status": "error", "ip": ip, "reason": "firewall rule failed"}

        blocked_ips[ip] = datetime.now()


    # Restriccion 2: programar la expiración del bloqueo 
    threading.Timer(BLOCK_DURATION_MINUTES * 60, unblock_ip, args=[ip]).start()

    log.info("IP %s BLOQUEADA (expira en %d min)", ip, BLOCK_DURATION_MINUTES)
    return {"status": "blocked", "ip": ip, "action": "firewall_block",
            "expires_in_minutes": BLOCK_DURATION_MINUTES}






def block_ip(ip:str) -> bool:
    # Creamos reglas de firewall para bloquear la IP
    # Devuelve True si tuvo exito, devuelve False si fallo

    rule_name = f"IDS_Block_{ip}"
    try:
        for direction in ("in", "out"):
            subprocess.run (
                ["netsh", "advfirewall", "firewall", "add", "rule",
                 f"name={rule_name}", f"dir={direction}",
                 "action=block", f"remoteip={ip}"],
                 check=True, capture_output=True, timeout=10
            )
        return True
    except subprocess.CalledProcessError as e:
        log.error("netsh fallo al bloquear %s: %s", ip, e.stderr.decode(errors="ignore"))
        return False
    except Exception as e:
        log.error("Error inesperado al bloquead %s: %s", ip, e)
        return False

def unblock_ip(ip:str) -> None:
    # Eliminamos las reglas de firewall de una IP
    rule_name = f"IDS_Block_{ip}"
    try:
        subprocess.run(
            ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={rule_name}"],
            check=True, capture_output=True, timeout=10    
        )    
        log.info("IP %s DESBLOQUEADA (Expiro el tiempo de bloqueo)", ip)
    except Exception as e:
        log.error("Error al desbloquear %s: %s", ip, e)
    finally:
        with _lock:
            blocked_ips.pop(ip, None)
    



# =========logging========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("ids_responses.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("ids-active-response")

if __name__ == "__main__":
    log.info("IDS active-response escuchando en 127.0.0.1:%d", LISTEN_PORT)
    app.run(host="127.0.0.1", port=LISTEN_PORT)
