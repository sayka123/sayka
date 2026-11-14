"""Read-only local file inspection; not BMW FDL decoding or vehicle programming."""

import hashlib
from pathlib import Path
import re
import xml.etree.ElementTree as ET

MAX_BYTES = 2 * 1024 * 1024
MAX_DIFF_ROWS = 2000


def _read(path):
    with open(path, 'rb') as file:
        data = file.read(MAX_BYTES + 1)
    if not data or len(data) > MAX_BYTES:
        raise ValueError('Dosya boş olamaz ve 2 MB sınırını aşamaz')
    return data


def _local(tag):
    return tag.rsplit('}', 1)[-1]


def load_fa(path):
    """Inspect the standardFA/saCodes layout in an exported FA XML file."""
    data = _read(path)
    try:
        # Normalize to text before rejecting DTD/entity declarations, including UTF-16.
        encoding = 'utf-16' if data.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig'
        text = data.decode(encoding)
        if '\x00' in text or re.search(r'<!\s*(DOCTYPE|ENTITY)', text, re.I):
            raise ValueError('DTD, entity veya tanınmayan XML kodlaması desteklenmez')
        root = ET.fromstring(text)
    except (UnicodeError, ET.ParseError) as error:
        raise ValueError('Geçerli UTF-8/UTF-16 FA XML dosyası okunamadı') from error
    fas = [node for node in root.iter() if _local(node.tag) == 'fa']
    if len(fas) != 1:
        raise ValueError('Dosya tam olarak bir fa öğesi içermeli; genel XML veya çoklu FA desteklenmez')
    fa = fas[0]
    standards = [node for node in fa if _local(node.tag) == 'standardFA']
    headers = [node for node in fa if _local(node.tag) == 'header']
    if len(standards) != 1 or len(headers) > 1:
        raise ValueError('Tek standardFA ve en fazla bir header öğesi gerekir')
    standard = standards[0]
    if not standard.get('series') or not standard.get('typeKey'):
        raise ValueError('standardFA series/typeKey alanları eksik')
    options = []
    for group in standard:
        if _local(group.tag) == 'saCodes':
            for item in group:
                if _local(item.tag) != 'saCode':
                    continue
                code = (item.text or '').strip()
                if not re.fullmatch(r'[A-Z0-9]{3}', code):
                    raise ValueError('saCode üç büyük harf/rakam olmalı')
                options.append(code)
    metadata = {name: standard.get(name) for name in
                ('series', 'typeKey', 'timeCriteria', 'colourCode', 'fabricCode', 'faVersion')}
    return {'file': Path(path).name, 'sha256': hashlib.sha256(data).hexdigest(),
            'metadata': metadata, 'sa_codes': sorted(set(options)),
            'vin_present': bool(headers and headers[0].get('vinLong')),
            'verified_against_vehicle': False}


def compare_binary(before_path, after_path):
    """Bounded raw byte comparison; extension and hashes cannot establish NCD validity."""
    before, after = _read(before_path), _read(after_path)
    rows, changed = [], 0
    for offset in range(0, max(len(before), len(after)), 16):
        old, new = before[offset:offset + 16], after[offset:offset + 16]
        if old == new:
            continue
        changed += sum((old[i] if i < len(old) else None) != (new[i] if i < len(new) else None)
                       for i in range(max(len(old), len(new))))
        if len(rows) < MAX_DIFF_ROWS:
            rows.append({'offset': offset, 'before': old.hex(' ').upper(), 'after': new.hex(' ').upper()})
    return {'before_size': len(before), 'after_size': len(after),
            'before_sha256': hashlib.sha256(before).hexdigest(),
            'after_sha256': hashlib.sha256(after).hexdigest(), 'changed_bytes': changed,
            'rows': rows, 'display_truncated': changed > 0 and len(rows) == MAX_DIFF_ROWS and
            any(before[offset:offset+16] != after[offset:offset+16]
                for offset in range(rows[-1]['offset']+16, max(len(before), len(after)), 16)),
            'semantic_decode': False}
