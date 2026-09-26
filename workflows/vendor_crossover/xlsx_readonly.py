"""Read-only, whitelisted OOXML decoding, with no third-party spreadsheet dependency.
Only call after explicit authorization. This module never changes an input workbook.
"""
from pathlib import PurePosixPath
import posixpath, re, zipfile, math
import xml.etree.ElementTree as ET
from guard import GuardError
NS='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
REL='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
ENDPOINTS={'PARPi':'rho:PARPi_vs_DMSO','WEE1i':'rho:WEE1i_vs_DMSO',
           'ATMi':'rho:ATMi_vs_DMSO','ATRi':'rho:ATRi_vs_DMSO','DNAPKi':'rho:DNAPKi_vs_DMSO'}

def colnum(ref):
    m=re.fullmatch(r'([A-Z]+)[0-9]+',ref)
    if not m: raise GuardError('Invalid OOXML cell address')
    out=0
    for a in m.group(1): out=out*26+ord(a)-64
    return out

def cell_value(c,strings):
    if c.find(NS+'f') is not None: raise GuardError('Formula in selected cell; cached formula not accepted')
    typ=c.attrib.get('t','n')
    if typ=='inlineStr':return ''.join(t.text or '' for t in c.iter(NS+'t'))
    v=c.find(NS+'v')
    if v is None or v.text is None:return None
    if typ=='s':
        i=int(v.text)
        if i<0 or i>=len(strings): raise GuardError('Shared string index outside table')
        return strings[i]
    if typ in ('str','e','b'):return v.text
    try:return float(v.text)
    except ValueError:raise GuardError('Unexpected nonnumeric numeric cell')

def workbook_parts(z,sheet_name):
    for i in z.infolist():
        if PurePosixPath(i.filename).is_absolute() or '..' in PurePosixPath(i.filename).parts:
            raise GuardError('Unsafe workbook member path')
    if sum(i.file_size for i in z.infolist())>1024**3: raise GuardError('Workbook expansion exceeds 1 GiB cap')
    wb=ET.fromstring(z.read('xl/workbook.xml'))
    matches=[s for s in wb.iter(NS+'sheet') if s.attrib.get('name')==sheet_name]
    if len(matches)!=1: raise GuardError('Expected unique sheet: '+sheet_name)
    rid=matches[0].attrib[REL+'id']
    rs=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    r=[e for e in rs if e.attrib.get('Id')==rid]
    if len(r)!=1 or r[0].attrib.get('TargetMode')=='External':raise GuardError('Invalid/external sheet relationship')
    target=r[0].attrib['Target']
    path=posixpath.normpath(target.lstrip('/') if target.startswith('/') else posixpath.join('xl',target))
    if not path.startswith('xl/') or '..' in PurePosixPath(path).parts:raise GuardError('Sheet outside xl')
    strings=[]
    if 'xl/sharedStrings.xml' in z.namelist():
        with z.open('xl/sharedStrings.xml') as f:
            for _,el in ET.iterparse(f,events=('end',)):
                if el.tag==NS+'si':
                    strings.append(''.join(t.text or '' for t in el.iter(NS+'t'))); el.clear()
    return path,strings

def read_headers(z,path,strings):
    headers=[]
    with z.open(path) as f:
        for _,el in ET.iterparse(f,events=('end',)):
            if el.tag!=NS+'row': continue
            rn=int(el.attrib['r'])
            if rn>3:break
            headers.append({colnum(c.attrib['r']):cell_value(c,strings) for c in el if c.tag==NS+'c'})
            el.clear()
    return headers

def find_block(headers,endpoint):
    candidates=set()
    for row in headers:
        for c,v in row.items():
            if isinstance(v,str) and v.strip()==endpoint+'|score':candidates.add(c)
    maxcol=max((max(r,default=0) for r in headers),default=0)
    for groups in headers:
        current=None
        for c in range(1,maxcol+1):
            value=groups.get(c)
            if isinstance(value,str) and (value.startswith('rho:') or value.startswith('gamma:')):
                current=value.strip().split('|')[0]
            if current==endpoint and any(str(r.get(c,'')).strip()=='score' for r in headers):
                candidates.add(c)
    if len(candidates)!=1:raise GuardError('Unresolved/ambiguous exact endpoint block: '+endpoint)
    score=next(iter(candidates))
    if score<3:raise GuardError('Endpoint lacks gene/transcript columns')
    return {'gene':score-2,'transcript':score-1,'score':score}

def read_allowed(path,expected_identities,background):
    """Requires unique original records. Diagnoses absent secondary endpoints, never shrinks G."""
    background=set(background); vectors={}; raw_records={}; issues=[]
    with zipfile.ZipFile(path) as z:
        sp,strings=workbook_parts(z,'Gene Level Phenotypes')
        headers=read_headers(z,sp,strings)
        blocks={}
        for role,endpoint in ENDPOINTS.items():
            try: blocks[role]=find_block(headers,endpoint)
            except GuardError as e:
                if role in ('PARPi','WEE1i'):raise
                issues.append({'role':role,'issue':str(e)})
        # Only a uniquely named DMSO gamma is accepted. No guessing or alias repair.
        gamma_names=set()
        for row in headers:
            for v in row.values():
                if isinstance(v,str):
                    v=v.strip().split('|')[0]
                    if v.startswith('gamma:') and 'DMSO' in v:gamma_names.add(v)
        if len(gamma_names)==1:
            try:blocks['gamma_DMSO']=find_block(headers,next(iter(gamma_names)))
            except GuardError as e:issues.append({'role':'gamma_DMSO','issue':str(e)})
        else:issues.append({'role':'gamma_DMSO','issue':'No unique verified DMSO gamma field'})
        for role in blocks: vectors[role]={};raw_records[role]=[]
        with z.open(sp) as f:
            for _,el in ET.iterparse(f,events=('end',)):
                if el.tag!=NS+'row':continue
                rn=int(el.attrib['r'])
                if rn<=3:el.clear();continue
                cells={colnum(c.attrib['r']):c for c in el if c.tag==NS+'c'}
                for role,b in blocks.items():
                    gene=cell_value(cells[b['gene']],strings) if b['gene'] in cells else None
                    if gene not in background:continue
                    if gene in vectors[role]:raise GuardError('Duplicate G identity in '+role+': '+gene)
                    transcript=cell_value(cells[b['transcript']],strings) if b['transcript'] in cells else None
                    if role in expected_identities:
                        expected=expected_identities[role][gene]
                        if rn!=expected['row'] or str(transcript)!=expected['transcript']:
                            raise GuardError('Frozen row/transcript mismatch in '+role+': '+gene)
                    value=cell_value(cells[b['score']],strings) if b['score'] in cells else None
                    if not isinstance(value,(int,float)) or not math.isfinite(value):
                        value=None
                    vectors[role][gene]=value
                    raw_records[role].append({'condition':role,'gene':gene,'xlsx_row':rn,'transcript':transcript,'raw_score':value})
                el.clear()
        for role in list(vectors):
            missing=background-set(vectors[role]); nonfinite=sum(v is None for v in vectors[role].values())
            if missing or nonfinite:
                issue={'role':role,'missing_G_n':len(missing),'nonfinite_G_n':nonfinite}
                if role in ('PARPi','WEE1i'):raise GuardError('Primary identity/value incomplete; no shrinking: '+str(issue))
                issues.append(issue);del vectors[role]
    return vectors,raw_records,{'sheet': 'Gene Level Phenotypes','verified_blocks':blocks,'issues':issues}
