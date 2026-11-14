"""Bounded tester-present scan; not an exhaustive BMW topology discovery."""
import time
from .hsfz import HsfzError, NoResponse
from .uds import ProtocolError


def scan(client, addresses, *, tester=None, stop=None, progress=None, timeout=0.8):
    addresses = list(addresses)
    if not addresses or len(addresses) > 256 or any(type(a) is not int or not 0 <= a <= 0xFFFF for a in addresses):
        raise ValueError('Tarama 1–256 geçerli adres gerektirir')
    addresses = list(dict.fromkeys(addresses))
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0.1 <= timeout <= 5:
        raise ValueError('Zaman aşımı 0.1–5 saniye olmalı')
    results, cancelled = [], False
    for address in addresses:
        if stop and stop():
            cancelled = True
            break
        if address == tester:
            state, error = 'skipped', None
            elapsed = 0
        else:
            start = time.monotonic()
            try:
                present = client.is_present(address, timeout=timeout)
                state, error = ('responded' if present else 'no_response'), None
            except NoResponse as exc:
                state, error = 'no_response', str(exc)
            except ProtocolError as exc:
                state, error = 'invalid_response', str(exc)
            except (OSError, HsfzError) as exc:
                state, error = 'transport_error', str(exc)
            elapsed = round((time.monotonic() - start)*1000, 1)
        row = dict(ecu=address, state=state, error=error, latency_ms=elapsed)
        results.append(row)
        if progress:
            progress(len(results), len(addresses), row)
        if state == 'transport_error':
            break
    return dict(requested=addresses, results=results, cancelled=cancelled,
                complete=len(results) == len(addresses) and not cancelled,
                exhaustive=False, read_at=time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                found=[row['ecu'] for row in results if row['state'] == 'responded'])
