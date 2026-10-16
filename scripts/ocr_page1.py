import json,subprocess,os,sys,csv,glob
import pytesseract
from PIL import Image
from scipy import stats
import numpy as np
base="data_sources/tier1_exam_grading/mendeley_sf3kvjwknt/A Dataset of Digitized Student Examination Papers,/Student_Pdf"
r={}
for l in open('outputs/experiments/track3/track3_predictions.jsonl'):
    x=json.loads(l); r[x['record_id']]=x
dpi=int(sys.argv[1])
from multiprocessing import Pool
def work(i):
    rid=f"MDLY-{i:04d}"
    pdf=f"{base}/Student_{i}.pdf"
    out=f"{os.environ['HOME']}/ijdar/f14/p{i}"
    subprocess.run(["pdftoppm","-f","1","-l","1","-r",str(dpi),"-png",pdf,out],check=True)
    png=glob.glob(out+"*.png")[0]
    d=pytesseract.image_to_data(Image.open(png),output_type=pytesseract.Output.DICT)
    words=[(t,float(c)) for t,c in zip(d['text'],d['conf']) if t.strip() and float(c)>=0]
    chars=sum(len(t) for t,_ in words); conf=np.mean([c for _,c in words]) if words else 0
    e=abs(r[rid]['pred_score']-r[rid]['true_score']) if r[rid]['pred_score'] is not None else np.nan
    os.remove(png)
    json.dump([(t,float(c)) for t,c in zip(d['text'],d['conf'])],open(f"{os.environ['HOME']}/ijdar/f14/w{dpi}_{i}.json",'w'))
    return (i,chars,conf,e,r[rid]['model'])
if __name__=='__main__':
  rows=Pool(os.cpu_count()).map(work,[i for i in range(1,51) if not os.path.exists(f"{os.environ['HOME']}/ijdar/f14/w{dpi}_{i}.json")])
  a=np.array([(c,f,e) for _,c,f,e,_ in rows]);m=~np.isnan(a[:,2])
  print(m.sum(),stats.pearsonr(a[m,0],a[m,2]),stats.pearsonr(a[m,1],a[m,2]))
  json.dump(rows,open(f"{os.environ['HOME']}/ijdar/f14/rows{dpi}.json","w"))
