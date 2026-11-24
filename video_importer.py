"""Dragonfire landscape member-list video -> review CSV. Requires local Tesseract."""
import argparse, csv, re, subprocess, tempfile
from pathlib import Path
import cv2
import numpy as np

def collect(video, template):
    cap=cv2.VideoCapture(str(video)); fps=cap.get(cv2.CAP_PROP_FPS) or 30
    groups=[]; i=0
    while True:
        ok, f=cap.read()
        if not ok: break
        i+=1
        if i%max(1,round(fps*.25)): continue
        f=cv2.resize(f,(1112,512))
        m=cv2.matchTemplate(f[185:510,466:493],template,cv2.TM_CCOEFF_NORMED)
        scores=m.max(axis=1)
        ys=[y+185 for y,s in enumerate(scores) if s>=.80 and s>=scores[max(0,y-6):y+7].max()]
        if len(ys)<3: continue
        for y in ys:
            if y<194 or y+25>510: continue
            row=f[y-3:y+25,265:607]; gray=cv2.cvtColor(row,cv2.COLOR_BGR2GRAY)
            # Match the text only, allowing a few pixels of vertical jitter.
            sig=gray[:,227:320]; quality=cv2.Laplacian(gray,cv2.CV_64F).var()
            best=None; score=0
            for g in groups:
                a=cv2.matchTemplate(np.pad(g['sig'],((3,3),(2,2)),mode='edge'),sig,cv2.TM_CCOEFF_NORMED).max()
                if a>score: best=g; score=a
            if score>.86:
                best['hits']+=1
                if quality>best['quality']: best.update(row=gray,sig=sig,quality=quality)
            else: groups.append(dict(row=gray,sig=sig,quality=quality,hits=1,time=i/fps))
    cap.release(); return groups

def recognize(groups):
    # Batch all text crops into a single image per column, one line per row.
    rows=[]
    for g in groups:
        gray=g['row']; parts=[]
        for crop in (gray[:,:195],gray[:,227:333]):
            z=cv2.resize(crop,None,fx=3,fy=3,interpolation=cv2.INTER_CUBIC)
            z=255-cv2.normalize(z,None,0,255,cv2.NORM_MINMAX)
            parts.append(z)
        rows.append(parts)
    if not rows: return []
    results=[]
    with tempfile.TemporaryDirectory() as td:
        for col in range(2):
            # Each row occupies 100 px, preserving coordinates in TSV output.
            w=max(r[col].shape[1] for r in rows)+40
            canvas=np.full((len(rows)*100,w),255,np.uint8)
            for i,r in enumerate(rows): canvas[i*100+8:i*100+8+r[col].shape[0],15:15+r[col].shape[1]]=r[col]
            p=Path(td)/f'col{col}.png'; cv2.imwrite(str(p),canvas)
            args=['tesseract',str(p),'stdout','--psm','6']
            if col: args+=['-c','tessedit_char_whitelist=0123456789,']
            tsv=subprocess.check_output(args+['tsv'],text=True,stderr=subprocess.DEVNULL)
            lines=['']*len(rows)
            for v in csv.DictReader(tsv.splitlines(),delimiter='\t'):
                if v['text'].strip():
                    k=int((int(v['top'])+int(v['height'])/2)//100)
                    if 0<=k<len(lines): lines[k]+=(' ' if lines[k] else '')+v['text']
            results.append(lines)
    return [dict(Player=n,Power=re.sub(r'\D','',p),Observations=g['hits'],First_second=round(g['time'],2)) for n,p,g in zip(*results,groups)]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('video'); ap.add_argument('--output',default='video_review.csv'); ap.add_argument('--template',default=str(Path(__file__).with_name('power_icon.png'))); args=ap.parse_args()
    template=cv2.imread(args.template)
    if template is None: raise SystemExit('Missing power_icon.png')
    groups=collect(args.video,template); rows=recognize(groups)
    with open(args.output,'w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=['Player','Power','Observations','First_second']); writer.writeheader();writer.writerows(rows)
    print(f'{len(rows)} candidate rows; review duplicates and OCR before importing.')
if __name__=='__main__': main()
