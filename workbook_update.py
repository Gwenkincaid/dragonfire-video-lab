"""Update a copy of the master workbook after human review."""
import io, re, math
from copy import copy
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

def directory(raw):
    w=load_workbook(io.BytesIO(raw),data_only=True)
    return {str(t): (f,n,a) for f,t,n,a,*_ in w['Alliance Directory'].values if f in ('Dorne','Westerlands','Stormlands','The Vale') and t and a}

def update(raw, tag, day, rows, timestamp, replace=False):
    w=load_workbook(io.BytesIO(raw)); s=w['Player Progress']; d=w['Alliance Directory']
    faction, name, label=directory(raw)[tag]
    headers={str(c.value).strip():c.column for c in s[1] if c.value is not None}
    pc,fc,ac=(headers[k] for k in ('Player','Faction','Alliance'))
    daycols=[c.column for c in s[1] if re.match(rf'^Day {day}(?!\d)',str(c.value))]
    if len(daycols)>1: raise ValueError('Duplicate day columns')
    dc=daycols[0] if daycols else s.max_column+1
    if not daycols: s.cell(1,dc,f'Day {day}')._style=copy(s.cell(1,2)._style)
    seen=set(); cleaned=[]
    for r in rows:
        p=str(r['Player']).strip(); v=float(r['Power']); key=p.casefold()
        if not p or p.lower() in ('nan','none','alliance power') or p.startswith('=') or key in seen or not math.isfinite(v) or v<=0 or v!=int(v): raise ValueError(f'Invalid or duplicate player/power: {p}')
        seen.add(key); cleaned.append((p,int(v)))
    if not cleaned: raise ValueError('No players')
    existing={}
    for i in range(2,s.max_row+1):
        p=s.cell(i,pc).value
        if p and str(p).casefold()!='alliance power':
            k=str(p).strip().casefold()
            if k in existing: raise ValueError(f'Duplicate existing name: {p}')
            existing[k]=i
    for p,v in cleaned:
        i=existing.get(p.casefold())
        if i and s.cell(i,ac).value not in (tag,label,None): raise ValueError(f'{p} belongs to another alliance. Resolve membership manually before import.')
        if i and s.cell(i,dc).value is not None and s.cell(i,dc).value!=v and not replace: raise ValueError(f'{p} already has Day {day} power. Enable replace only if intended.')
    if replace:
        for i in existing.values():
            if s.cell(i,ac).value in (tag,label): s.cell(i,dc).value=None
    for p,v in cleaned:
        i=existing.get(p.casefold())
        if i is None:
            i=s.max_row+1
            for j in range(1,s.max_column+1): s.cell(i,j)._style=copy(s.cell(2,j)._style)
            s.cell(i,pc,p)
        s.cell(i,fc,faction); s.cell(i,ac,label); s.cell(i,dc,v).number_format='#,##0'
    # Remove obsolete MOON total row, which is not a player observation.
    for i in range(s.max_row,1,-1):
        if str(s.cell(i,pc).value).casefold()=='alliance power':
            for c in s[i]: c.value=None
    s.auto_filter.ref=f'A1:{get_column_letter(s.max_column)}{s.max_row}'
    # Existing directory has reported totals; keep its historical values and update only approved snapshot.
    dd=[c.column for c in d[1] if re.match(rf'^Day {day}(?!\d)',str(c.value))]
    if not dd: dd=[d.max_column+1];d.cell(1,dd[0],f'Day {day}')
    for i in range(2,d.max_row+1):
        if d.cell(i,2).value==tag: d.cell(i,dd[0],sum(v for _,v in cleaned)).number_format='#,##0'
    log=w['Snapshot Log'] if 'Snapshot Log' in w.sheetnames else w.create_sheet('Snapshot Log')
    if log.max_row==1 and log.cell(1,1).value is None:
        for j,h in enumerate(['Alliance','Faction','Day','UTC timestamp','Members','Recorded power'],1):log.cell(1,j,h)
    log.append([tag,faction,day,timestamp,len(cleaned),sum(v for _,v in cleaned)])
    out=io.BytesIO();w.save(out);return out.getvalue()
