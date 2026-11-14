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
                    timeout=2.0, preferred=None):
    """Returns a connected transport. With protocol=None, HSFZ is tried first, then DoIP."""
    attempts = {
        "hsfz": lambda: hsfz.HsfzConnection(host, port=hsfz_port, timeout=timeout),
        "doip": lambda: doip.DoipConnection(host, port=doip_port, timeout=timeout),
    }
    if protocol not in (None, "hsfz", "doip") or preferred not in (None, "hsfz", "doip"):
        raise ValueError("Protokol doip, hsfz veya otomatik olmalı")
    order = [protocol] if protocol else ([preferred, "hsfz" if preferred == "doip" else "doip"]
                                        if preferred else ["hsfz", "doip"])
    errors = []
    for name in order:
        conn = attempts[name]()
        try:
            conn.connect()
            conn.protocol = name
            return conn
        except (OSError, hsfz.HsfzError) as e:
            conn.close()
            port = doip_port if name == "doip" else hsfz_port
            errors.append(f"{name.upper()} TCP {port}: {e}")
    raise hsfz.HsfzError("Araca bağlanılamadı. " + " | ".join(errors) +
                        "\n\nConnection refused: seçilen IP/port bağlantıyı reddetti; bu bir kodlama kilidi kanıtı değildir. "
                        "Mac'in kendi Ethernet IP'sini değil aracın IP'sini seçin. "
                        "Aracı otomatik bul ile yeniden arayın; Ethernet DHCP, kablo ve araç uyanıklığını kontrol edin. "
                        "Diğer teşhis uygulamalarını kapatın. Güvenlik duvarını bütünüyle kapatmayın.")
