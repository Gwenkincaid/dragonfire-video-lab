import io, tempfile, hmac, hashlib, shutil
from pathlib import Path
from datetime import datetime, timezone
import cv2, pandas as pd, streamlit as st
from video_importer import collect, recognize
from workbook_update import directory, update
ROOT=Path(__file__).parent
st.set_page_config(page_title='Dragonfire | Video Lab',page_icon='🐉',layout='wide')
st.title('🐉 Dragonfire · Video Lab')
try: secret=str(st.secrets['ADMIN_PASSWORD'])
except Exception: secret=''
if not secret: st.error('Set ADMIN_PASSWORD in Streamlit Secrets.');st.stop()
if not st.session_state.get('authorized'):
    with st.form('login'):
        pw=st.text_input('Admin password',type='password'); submit=st.form_submit_button('Unlock')
    if submit and hmac.compare_digest(pw.encode(),secret.encode()): st.session_state.authorized=True;st.rerun()
    if submit: st.error('Incorrect password')
    st.stop()
if st.sidebar.button('Lock'): st.session_state.clear();st.rerun()
base=st.file_uploader('1. Latest master workbook (required)',type=['xlsx'])
if not base: st.info('Upload your latest workbook; use the included progress.xlsx for the first test.');st.stop()
raw=base.getvalue()
try: alliances=directory(raw)
except Exception as e: st.error(f'Workbook format: {e}');st.stop()
faction=st.selectbox('Faction',['Dorne','Westerlands','Stormlands','The Vale'])
tag=st.selectbox('Alliance',[t for t,a in alliances.items() if a[0]==faction],format_func=lambda t:alliances[t][2])
day=st.number_input('Report day',min_value=1,value=6,step=1)
now=datetime.now(timezone.utc)
date=st.date_input('Capture date (UTC)',value=now.date());time=st.time_input('Capture time (UTC)',value=now.time().replace(second=0,microsecond=0))
expected=st.number_input('Expected member count',min_value=1,value=47,step=1)
mode=st.radio('Source',['Video','Reviewed CSV'])
source=st.file_uploader('2. Upload recording or reviewed CSV',type=['mp4','mov'] if mode=='Video' else ['csv'])
if not source:st.stop()
key=hashlib.sha256(source.getvalue()).hexdigest()+hashlib.sha256(raw).hexdigest()+tag+mode
if st.session_state.get('source_key')!=key:
    for k in ['rows','images','output']:st.session_state.pop(k,None)
    st.session_state.source_key=key
if st.button('Extract player data',type='primary'):
    try:
        if mode=='Video':
            if not shutil.which('tesseract'):raise RuntimeError('Tesseract is missing. Check packages.txt.')
            with st.spinner('Extracting video frames and recognizing text…'):
                with tempfile.TemporaryDirectory() as td:
                    p=Path(td)/('recording'+Path(source.name).suffix);p.write_bytes(source.getvalue())
                    groups=collect(p,cv2.imread(str(ROOT/'power_icon.png'))); rows=recognize(groups)
                st.session_state.images=[g['row'] for g in groups]
        else:
            df=pd.read_csv(io.BytesIO(source.getvalue()));rows=df[['Player','Power']].to_dict('records');st.session_state.images=[]
        df=pd.DataFrame(rows)
        if df.empty:raise ValueError('No rows detected')
        df['Power']=pd.to_numeric(df['Power'],errors='coerce');df.insert(0,'Row',range(1,len(df)+1));st.session_state.rows=df
        st.session_state.pop('output',None)
    except Exception as e:st.error(str(e))
if 'rows' not in st.session_state:st.stop()
st.subheader('3. Review every player and power value')
left,right=st.columns([3,2])
with left:
    edited=st.data_editor(st.session_state.rows,num_rows='dynamic',hide_index=True,key='editor_'+key,column_config={'Power':st.column_config.NumberColumn(format='%d',min_value=1),'Row':st.column_config.NumberColumn(disabled=True)})
with right:
    imgs=st.session_state.images
    if imgs:
        i=st.number_input('Original video row',min_value=1,max_value=len(imgs),value=1);st.image(imgs[i-1],width=350,caption=f'Original row {i}')
st.metric('Reviewed rows',len(edited));st.metric('Recorded power',f"{edited.Power.sum():,.0f}")
if len(edited)!=expected:st.warning('Count differs from expected. Fix the rows or record again.')
st.download_button('Download reviewed CSV',edited.to_csv(index=False).encode('utf-8-sig'),'reviewed.csv','text/csv')
replace=st.checkbox('Replace existing values for this alliance and report day (clears that alliance’s old day values)')
confirm=st.checkbox('I verified names, powers, membership and capture time against the recording.')
if st.button('Build updated workbook',disabled=not confirm or len(edited)!=expected):
    try:
        out=update(raw,tag,int(day),edited.to_dict('records'),datetime.combine(date,time).isoformat()+'Z',replace)
        st.session_state.output=out;st.success('Workbook copy prepared. Download it and use it for the next import.')
    except Exception as e:st.error(str(e))
if 'output' in st.session_state:st.download_button('Download updated progress.xlsx',st.session_state.output,'progress.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
