"""Picks the right transport: HSFZ (port 6801, F/G series) or DoIP (port 13400, newer cars such as iX)."""

from . import doip, hsfz


def discover_all(target="255.255.255.255", timeout=2.0, hsfz_port=hsfz.DISCOVERY_PORT,
                 doip_port=doip.DOIP_PORT):
    cars = {}
    for c in hsfz.discover(target, port=hsfz_port, timeout=timeout / 2):
        c["protocol"] = "hsfz"
        cars[c["ip"]] = c
    for c in doip.discover(target, port=doip_port, timeout=timeout / 2):
        cars.setdefault(c["ip"], c)
    return list(cars.values())


def open_connection(host, protocol=None, hsfz_port=hsfz.DIAG_PORT, doip_port=doip.DOIP_PORT,
                    timeout=2.0):
    """Returns a connected transport. With protocol=None, HSFZ is tried first, then DoIP."""
    attempts = {
        "hsfz": lambda: hsfz.HsfzConnection(host, port=hsfz_port, timeout=timeout),
        "doip": lambda: doip.DoipConnection(host, port=doip_port, timeout=timeout),
    }
    order = [protocol] if protocol else ["hsfz", "doip"]
    errors = []
    for name in order:
        conn = attempts[name]()
        try:
            conn.connect()
            conn.protocol = name
            return conn
        except (OSError, hsfz.HsfzError) as e:
            conn.close()
            errors.append(f"{name.upper()}: {e}")
    raise hsfz.HsfzError("Araca bağlanılamadı. " + " | ".join(errors))
