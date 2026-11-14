"""Picks the right transport: HSFZ (port 6801, F/G series) or DoIP (port 13400, newer cars such as iX)."""

from . import doip, hsfz
import ipaddress
from concurrent.futures import ThreadPoolExecutor
import errno


def connection_error_kind(error):
    chain, seen = error, set()
    while chain is not None and id(chain) not in seen:
        seen.add(id(chain))
        if isinstance(chain, TimeoutError):
            return 'timeout'
        if isinstance(chain, ConnectionRefusedError) or getattr(chain, 'errno', None) in (errno.ECONNREFUSED, 61, 10061):
            return 'refused'
        chain = chain.__cause__
    return 'other'


def discover_all(target="255.255.255.255", timeout=2.0, hsfz_port=hsfz.DISCOVERY_PORT,
                 doip_port=doip.DOIP_PORT, source_ip=None):
    if source_ip:
        address = ipaddress.IPv4Address(source_ip)
        if address.is_unspecified or address.is_multicast or str(address) == '255.255.255.255':
            raise ValueError("Geçerli yerel Ethernet IPv4 adresini girin")
    def search(function, port):
        try:
            args = dict(port=port, timeout=timeout)
            if source_ip:
                args['source_ip'] = source_ip
            return function(target, **args), None
        except OSError as error:
            return [], str(error)
    cars, errors = {}, []
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = [(name, pool.submit(search, function, port)) for name, function, port in
                [('hsfz', hsfz.discover, hsfz_port), ('doip', doip.discover, doip_port)]]
        for name, job in jobs:
            found, error = job.result()
            if error:
                errors.append(f"{name}: {error}")
            for candidate in found:
                candidate['protocol'] = name
                if candidate['ip'] != source_ip:
                    cars.setdefault(candidate['ip'], candidate)
    if errors and not cars:
        raise hsfz.HsfzError("Keşif ağ hatası: " + ' | '.join(errors))
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
    errors, kinds = [], []
    for name in order:
        conn = attempts[name]()
        try:
            conn.connect()
            conn.protocol = name
            return conn
        except (OSError, hsfz.HsfzError) as e:
            conn.close()
            port = doip_port if name == "doip" else hsfz_port
            kinds.append(connection_error_kind(e))
            errors.append(f"{name.upper()} TCP {port}: {e}")
    details = []
    if 'timeout' in kinds:
        details.append("Zaman aşımı: hedef IP/port bağlantı kurma veya protokol aşamasını süresinde tamamlamadı; reddedildiği kanıtlanmadı.")
    if 'refused' in kinds:
        details.append("Bağlantı reddi: hedef IP/port TCP bağlantısını kabul etmedi.")
    raise hsfz.HsfzError("Araca bağlanılamadı. " + " | ".join(errors) +
                        "\n\n" + ' '.join(details) + " Bu sonuç bir kodlama kilidi kanıtı değildir. "
                        "Mac'in kendi Ethernet IP'sini değil aracın IP'sini seçin. "
                        "Aracı otomatik bul ile yeniden arayın; Ethernet DHCP, kablo ve araç uyanıklığını kontrol edin. "
                        "Diğer teşhis uygulamalarını kapatın. Güvenlik duvarını bütünüyle kapatmayın.")
