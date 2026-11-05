import json,numpy as np,glob,sys
from sklearn.metrics import roc_auc_score
def load(p): return {x['record_id']:x for x in map(json.loads,open(p))}
ann={}
for f in glob.glob('/home/claude/evalbench/outputs/experiments/fixed_model/*.jsonl'): print(f)
def met(rows,ids,name):
    rows=[rows[i] for i in ids if rows[i].get('pred_score') is not None]
    p=np.array([r['pred_score'] for r in rows]);t=np.array([r['true_score'] for r in rows])
    rng=np.random.default_rng(42);n=len(p);idx=[rng.integers(0,n,n) for _ in range(10000)]
    mae=abs(p-t).mean();ci=np.percentile([abs(p[i]-t[i]).mean() for i in idx],[2.5,97.5])
    r=np.corrcoef(p,t)[0,1];rci=np.nanpercentile([np.corrcoef(p[i],t[i])[0,1] for i in idx],[2.5,97.5])
    out=f"{name}: n={n} MAE {mae:.2f} [{ci[0]:.2f},{ci[1]:.2f}] r {r:.3f} [{rci[0]:.3f},{rci[1]:.3f}] bias {np.mean(p-t):+.2f}"
    if rows[0].get('confidence') is not None:
        c=np.array([x['confidence'] for x in rows]);y=(abs(p-t)<=3).astype(int)
        au=roc_auc_score(y,c) if 0<y.sum()<n else float('nan')
        bins=np.linspace(0,1,11);e=0
        for a,b in zip(bins[:-1],bins[1:]):
            m=(c>=a)&((c<b)|(b==1))
            if m.any(): e+=m.mean()*abs(c[m].mean()-y[m].mean())
        out+=f" | AUROC {au:.3f} ECE {e:.3f} Brier {np.mean((c-y)**2):.3f} acc3 {y.mean():.2f} meanconf {c.mean():.2f}"
    print(out);return p,t
D='outputs/run1/'
e1=load(D+'e1t3_predictions.jsonl');e5=load(D+'e1t5_predictions.jsonl');e3=load(D+'e3b_predictions.jsonl')
ids=sorted(e1)
p,t=met(e1,ids,'clean page1 T3');met(e5,sorted(e5),'clean page1 T5');met(e3,sorted(e3),'indep. grading 4pp T3b')
print('mean-predictor MAE',abs(t-t.mean()).mean(),' SD',t.std())
print('e3b mcq mean',np.mean([x['mcq_score'] for x in e3.values() if x['mcq_score'] is not None]),'short mean',np.mean([x['short_score'] for x in e3.values() if x['short_score'] is not None]),'true mean',t.mean())
