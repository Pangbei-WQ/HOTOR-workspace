"""Read-only OOXML evidence extraction. Never recalculate or save source workbooks."""
import hashlib
import json
import re
import shutil
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET
from openpyxl.formula.translate import Translator

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
TAG = '{' + NS['m'] + '}'
INPUTS = [
    (Path(r'C:\Users\HDKJ\Desktop\跨境订货在线表.xlsx'), 17048666, 14),
    (Path(r'C:\Users\HDKJ\Desktop\跨境订货表汇总测算底表.xlsx'), 55275555, 17),
    (ROOT / '原件存档/下单盘点-工具表-伟卿_v1_20261106.xlsx', None, 14),
]

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def extract(path):
    with zipfile.ZipFile(path) as book:
        shared = []
        if 'xl/sharedStrings.xml' in book.namelist():
            shared = [''.join(x.itertext()) for x in ET.fromstring(book.read('xl/sharedStrings.xml'))]
        relationships = {x.get('Id'): x.get('Target') for x in ET.fromstring(book.read('xl/_rels/workbook.xml.rels'))}
        result = {'file': str(path), 'original_name': path.name, 'bytes': path.stat().st_size,
                  'sha256': digest(path), 'sheets': [], 'external_links': []}
        for name in book.namelist():
            if name.startswith('xl/externalLinks/_rels/') and name.endswith('.rels'):
                result['external_links'].append({'part': name, 'relationships': book.read(name).decode('utf-8')})
        workbook = ET.fromstring(book.read('xl/workbook.xml'))
        for sheet in workbook.find('m:sheets', NS):
            target = relationships[sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')]
            part = target.lstrip('/') if target.startswith('/') else 'xl/' + target
            item = {'name': sheet.get('name'), 'sheet_id': sheet.get('sheetId'), 'state': sheet.get('state'), 'part': part, 'cells': []}
            # Sample rows include headers, parameters and first actual SKU records.
            # Do not treat the sample as full-workbook coverage.
            limit = 520 if sheet.get('name') == 'SKU对应关系' else (60 if sheet.get('name') in ['下单发货', '0', '马来订货表', '印尼订货表'] else 16)
            masters = {}
            with book.open(part) as stream:
                for event, row in ET.iterparse(stream, events=['end']):
                    if row.tag != TAG + 'row':
                        continue
                    if int(row.get('r')) > limit:
                        break
                    for cell in row.findall('m:c', NS):
                        formula = cell.find('m:f', NS)
                        value = cell.find('m:v', NS)
                        text = value.text if value is not None else None
                        if cell.get('t') == 's' and text:
                            text = shared[int(text)]
                        if cell.get('t') == 'inlineStr':
                            text = ''.join(cell.find('m:is', NS).itertext())
                        if text is None and formula is None:
                            continue
                        record = {'cell': cell.get('r'), 'value': text, 'type': cell.get('t')}
                        if formula is not None:
                            record['formula'] = formula.text
                            record['formula_attributes'] = formula.attrib
                            if formula.get('t') == 'shared':
                                key = formula.get('si')
                                if formula.text:
                                    masters[key] = (cell.get('r'), formula.text)
                                elif key in masters:
                                    origin, original = masters[key]
                                    record['resolved_formula'] = Translator('=' + original, origin=origin).translate_formula(cell.get('r'))[1:]
                                    record['resolved_from'] = origin
                        item['cells'].append(record)
                    row.clear()
            result['sheets'].append(item)
        return result

def main():
    results = []
    for path, expected_bytes, expected_sheets in INPUTS:
        if expected_bytes is not None and path.stat().st_size != expected_bytes:
            raise ValueError(f'BASELINE_CHANGED {path}')
        result = extract(path)
        if len(result['sheets']) != expected_sheets:
            raise ValueError(f'SHEET_COUNT_CHANGED {path}')
        if expected_bytes is not None:
            archive = ROOT / '原件存档' / (path.stem + '_v1_20261106.xlsx')
            if archive.exists():
                if digest(archive) != result['sha256']:
                    raise ValueError(f'ARCHIVE_CONFLICT {archive}')
            else:
                shutil.copy2(path, archive)
            assert digest(archive) == result['sha256']
            result['archive'] = str(archive)
        results.append(result)
        print(path.name, result['bytes'], len(result['sheets']), result['sha256'])
    payload = {'generated_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
               'scope': 'Read-only first 16/60 rows per sheet; saved values, not recalculation', 'workbooks': results}
    (OUT / '公式证据.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print('EVIDENCE_SAVED', sum(len(s['cells']) for b in results for s in b['sheets']), 'cells')

if __name__ == '__main__':
    main()
