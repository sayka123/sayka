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


def _load_fa(path):
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
    summary = {'file': Path(path).name, 'sha256': hashlib.sha256(data).hexdigest(),
            'metadata': metadata, 'sa_codes': sorted(set(options)),
            'vin_present': bool(headers and headers[0].get('vinLong')),
            'verified_against_vehicle': False}
    vin = headers[0].get('vinLong', '').strip() if headers else ''
    return summary, vin


def load_fa(path):
    """Return the display summary without exposing VIN content."""
    return _load_fa(path)[0]


def compare_fa(before_path, after_path):
    """Compare supported metadata and SA codes, not complete FA semantics."""
    before, vin_before = _load_fa(before_path)
    after, vin_after = _load_fa(after_path)
    if vin_before and vin_after and vin_before != vin_after:
        raise ValueError('Dosyalardaki VIN değerleri farklı; aynı aracın FA karşılaştırması yapılamaz')
    rows = []
    for key in before['metadata']:
        old, new = before['metadata'][key], after['metadata'][key]
        if old != new:
            rows.append({'group': 'standardFA', 'field': key, 'before': old, 'after': new,
                         'change': 'Değişti'})
    old_codes, new_codes = set(before['sa_codes']), set(after['sa_codes'])
    for code in sorted(old_codes - new_codes):
        rows.append({'group': 'saCode', 'field': code, 'before': code, 'after': None,
                     'change': 'Dosyada çıkarılmış'})
    for code in sorted(new_codes - old_codes):
        rows.append({'group': 'saCode', 'field': code, 'before': None, 'after': code,
                     'change': 'Dosyada eklenmiş'})
    return {'format': 'bimmertool-fa-comparison-v1', 'before': before, 'after': after,
            'identity': 'file_vins_match' if vin_before and vin_after else 'unknown',
            'rows': rows, 'vehicle_verified': False, 'write_performed': False,
            'scope': 'Yalnızca standardFA alanları ve saCodes. eCodes, hoCodes ve diğer XML alanları '
                     'karşılaştırılmaz. Dosya farkı, donanımın takıldığını veya VO kodlama yapıldığını kanıtlamaz.'}


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
