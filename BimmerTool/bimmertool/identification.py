"""Standard UDS identification reads, not BMW CAFD/SVT decoding."""

import time

from .hsfz import NoResponse, HsfzError
from .uds import NegativeResponse, ProtocolError

# ISO-defined names, as enumerated by udsoncan.common.dids; support is ECU-specific.
FIELDS = (
    (0xF187, 'Üretici yedek parça numarası'),
    (0xF188, 'Üretici ECU yazılım numarası'),
    (0xF189, 'Üretici ECU yazılım sürümü'),
    (0xF191, 'Üretici ECU donanım numarası'),
    (0xF194, 'Tedarikçi ECU yazılım numarası'),
    (0xF195, 'Tedarikçi ECU yazılım sürümü'),
)


def read_identification(client, ecu, *, simulator=False):
    if type(ecu) is not int or not 0 <= ecu <= 0xFFFF:
        raise ValueError('Modül adresi 0x0000–0xFFFF aralığında tam sayı olmalı')
    if type(simulator) is not bool:
        raise ValueError('simulator must be boolean')
    rows = []
    for did, name in FIELDS:
        started = time.monotonic()
        row = dict(did=did, name=name, state=None, raw=None, ascii=None, error=None, nrc=None)
        try:
            data = client.read_did(ecu, did, timeout=1.0)
            if not isinstance(data, bytes) or not data:
                raise ProtocolError('Boş veya geçersiz kimlik verisi')
            row['raw'] = data.hex(' ').upper()
            text = data.rstrip(b'\0 ')
            row['ascii'] = text.decode('ascii') if text and all(32 <= b <= 126 for b in text) else None
            row['state'] = 'read'
        except NegativeResponse as error:
            row.update(state='refused', error=str(error), nrc=error.nrc)
        except NoResponse as error:
            row.update(state='no_response', error=str(error))
        except ProtocolError as error:
            row.update(state='invalid_response', error=str(error))
        except (OSError, HsfzError) as error:
            row.update(state='transport_error', error=str(error))
        row['latency_ms'] = round((time.monotonic() - started) * 1000, 1)
        rows.append(row)
        if row['state'] == 'transport_error':
            break
    return dict(format='bimmertool-ecu-identification-v1', ecu=ecu,
                source='simulator' if simulator else 'vehicle',
                read_at=time.strftime('%Y-%m-%dT%H:%M:%S%z'), results=rows,
                cafd_verified=False, module_type_verified=False,
                note='Standart DID kimlik yanıtları; CAFD, SVT, I-Step veya HU_MGU4 doğrulaması değildir. '
                     'ASCII sütunu yalnızca yazdırılabilir baytların metin görünümüdür; hex veri korunur.')
