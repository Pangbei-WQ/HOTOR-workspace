"""Independent offline checks; source workbooks remain read-only."""
import hashlib
import json
import math
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

OUT = Path(__file__).resolve().parent
DATA = json.loads((OUT / '公式证据.json').read_text(encoding='utf-8'))
RESULTS = []

def cell(book, sheet, address):
    b = DATA['workbooks'][book]
    s = next(s for s in b['sheets'] if s['name'] == sheet)
    return next((c for c in s['cells'] if c['cell'] == address), {'cell': address, 'value': None})

def number(book, sheet, address):
    value = cell(book, sheet, address)['value']
    if value is None or str(value).startswith('#'):
        raise ValueError(f'UNAVAILABLE {sheet}!{address}={value}')
    return float(value)

def record(name, actual, expected, note):
    assert actual == expected, (name, actual, expected)
    RESULTS.append({'name': name, 'actual': actual, 'expected': expected, 'note': note, 'passed': True})
    print('PASS', name, actual)

def guarded_boxes(demand, size):
    if size is None or size <= 0:
        raise ValueError('MISSING_OR_ZERO_BOX_SIZE')
    return math.ceil(max(0, demand) / size)

def require_unique_po(rows):
    keys = [(r['sku'], r['po']) for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError('DUPLICATE_SKU_PO')

def round_sheet(value):
    return int(Decimal(str(value)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def main():
    for book in DATA['workbooks']:
        path = Path(book['file'])
        with path.open('rb') as stream:
            current = hashlib.file_digest(stream, 'sha256').hexdigest()
        record('source_unchanged:' + path.name, current, book['sha256'], 'Original bytes, not an exported copy')
        if 'archive' in book:
            with Path(book['archive']).open('rb') as stream:
                record('archive_matches:' + path.name, hashlib.file_digest(stream, 'sha256').hexdigest(), current, 'Versioned copy')
    s = '下单汇总'
    record('real_shoe_SKU', cell(2,s,'E6')['value'], 'US4122BL', 'Actual saved source SKU')
    approved = number(2,s,'I6')
    size = number(2,s,'T6')
    boxes = guarded_boxes(approved, size)
    record('real_purchase_boxes', boxes, 938, 'ceil(15000/16)')
    record('real_purchase_quantity', boxes*size, number(2,s,'X6'), '15008 matches saved X6; independent arithmetic, not Google recalc')
    record('real_purchase_box_cache', boxes, number(2,s,'U6'), '938 matches saved U6')
    record('real_shipment_approved', number(2,'发货汇总','I3'), 15000.0, 'Approval quantity only; actual shipment evidence absent')
    record('real_shipment_batch_unavailable', cell(2,'发货汇总','T3')['value'], '#REF!', 'Do not coerce into zero')
    s = '马来订货表'
    deficit = (number(0,s,'CF7')+number(0,s,'H3'))*number(0,s,'BJ7') - sum(number(0,s,c+'7') for c in ['BS','BT','BU'])
    record('attachment_real_recommended_boxes', guarded_boxes(deficit,number(0,s,'BX7')),number(0,s,'CC7'),'K0301058: ceil(((7+9)*6-0)/5)=20 boxes')
    record('attachment_not_executed', number(0,s,'CA7'), 0.0, 'CA=BZ*BX, BZ blank; recommended 20 boxes is not committed quantity')
    record('same_workbook_external_source', '跨境订货表汇总测算底表.xlsx' in DATA['workbooks'][0]['external_links'][0]['relationships'],True,'OOXML external-link target establishes two-file relationship')
    # Exact boundaries from source formula design, using stated hypothetical inputs.
    record('order_window_days', len([x for x in range(30) if 0 <= x < 14]),14,'W uses >=O and <O+14')
    record('ship_window_days',len([x for x in range(-20,21) if -6 <= x <= 8]),15,'AF includes both endpoints')
    record('MOQ_nearest_can_underfill',round_sheet(740/500)*500,500,'W: ratio>=1 uses ROUND, not universal CEILING; hypothetical 740 demand')
    record('MOQ_below_minimum',math.ceil(200/500)*500,500,'W: ratio<1 uses CEILING; hypothetical 200 demand')
    record('safety_equal_W_trigger',30<30,False,'W tests V<I strictly')
    record('safety_equal_AG',0 if 30>30 else (30-30)*10+150,150,'AG tests AC>I; equality still returns AF; hypothetical inputs')
    d=datetime(1899,12,30)+timedelta(days=46432)
    record('arrival_anchor_sunday',d.weekday(),6,'Saved O4 and -WEEKDAY(...,2)+7: Sunday, not Monday')
    # Inject bad evidence, expose actual failure, then restore valid input.
    for label, action in [
        ('missing_source',lambda:number(2,'发货汇总','T3')),
        ('zero_box',lambda:guarded_boxes(16,0)),
        ('duplicate_po',lambda:require_unique_po([{'sku':'TEST','po':'PO1'},{'sku':'TEST','po':'PO1'}])),
    ]:
        try:
            action()
        except ValueError as error:
            print('EXPECTED_RED',label,str(error))
            RESULTS.append({'name':label,'expected_failure':str(error),'passed':True,'scope':'Offline audit guard, NOT a test of inaccessible Apps Script'})
        else:
            raise AssertionError('FAILURE_NOT_DETECTED '+label)
    record('restored_valid_box',guarded_boxes(16,8),2,'GREEN after zero-box injection')
    require_unique_po([{'sku':'TEST','po':'PO1'},{'sku':'TEST','po':'PO1.2'}])
    record('restored_unique_po',True,True,'Audit only: actual split-PO script behavior remains unverified')
    (OUT/'校验结果.json').write_text(json.dumps({'scope':'Independent arithmetic and offline audit guards; no Google or Apps Script execution','checks':RESULTS},ensure_ascii=False,indent=2),encoding='utf-8')
    print('ALL_CHECKS_PASSED',len(RESULTS))

if __name__ == '__main__':
    main()
