"""Live engine data via the standardised OBD DIDs (0xF400 + OBD PID) on the DME."""

from .hsfz import NoResponse

DME = 0x12


def _u16(b):
    return b[0] * 256 + b[1]


LIVE_VALUES = [
    # (name, unit, did, decoder)
    ("Motor devri", "dev/dk", 0xF40C, lambda b: _u16(b) / 4),
    ("Araç hızı", "km/s", 0xF40D, lambda b: b[0]),
    ("Soğutma suyu sıcaklığı", "°C", 0xF405, lambda b: b[0] - 40),
    ("Emme havası sıcaklığı", "°C", 0xF40F, lambda b: b[0] - 40),
    ("Motor yükü", "%", 0xF404, lambda b: b[0] * 100 / 255),
    ("Gaz kelebeği", "%", 0xF411, lambda b: b[0] * 100 / 255),
    ("Emme manifold basıncı", "kPa", 0xF40B, lambda b: b[0]),
    ("Akü / modül voltajı", "V", 0xF442, lambda b: _u16(b) / 1000),
]


def read_custom(client, ecu, did):
    """Raw value of any DID, for modules without standard values (e.g. EV battery/motor on iX)."""
    data = client.read_did(ecu, did, timeout=1.0)
    text = data.hex(" ").upper()
    if 1 <= len(data) <= 4:
        text += f"  (= {int.from_bytes(data, 'big')})"
    return text


def read_all(client, ecu=DME):
    """Returns [(name, value_or_None, unit, error_or_None)]."""
    out = []
    absent = None
    for name, unit, did, decode in LIVE_VALUES:
        if absent:
            out.append((name, None, unit, absent))
            continue
        try:
            data = client.read_did(ecu, did, timeout=1.0)
            out.append((name, round(decode(data), 1), unit, None))
        except NoResponse as e:
            # No engine module (e.g. electric cars): don't wait out every remaining value.
            absent = str(e)
            out.append((name, None, unit, absent))
        except Exception as e:  # one unsupported value must not stop the rest
            out.append((name, None, unit, str(e)))
    return out
