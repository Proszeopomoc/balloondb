import json
from pathlib import Path
DEFAULT_PACKS=["code_seeds.bpack","code_bridges.bpack","code_routes.bpack","code_results.bpack","code_patterns.bpack"]
ID_KEYS=["id","seed_id","pattern_id","route_id","bridge_id","result_id","name","status","result"]
def iter_strings(obj):
    if isinstance(obj,str): yield obj
    elif isinstance(obj,dict):
        for k,v in obj.items():
            if isinstance(k,str): yield k
            yield from iter_strings(v)
    elif isinstance(obj,list):
        for x in obj: yield from iter_strings(x)
def short(obj,n=220):
    s=json.dumps(obj,ensure_ascii=False,sort_keys=True)
    return s[:n]+("..." if len(s)>n else "")
def record_id(rec,fallback):
    if isinstance(rec,dict):
        for k in ID_KEYS:
            v=rec.get(k)
            if isinstance(v,str) and v: return v
    return fallback
def find_pack(root,pack):
    for p in [root/pack, root/"PACKS"/pack, root/"packs"/pack]:
        if p.exists(): return p
    return None
class MemorySnapshot:
    def __init__(self,root,records,report):
        self.memory_root=str(root); self.records=records; self.load_report=report
    def find_seed(self,text,limit=10):
        q=str(text).lower(); hits=[]
        for rec in self.records:
            score=0
            for s in iter_strings(rec['record']):
                sl=s.lower()
                if sl==q: score=max(score,100)
                elif q in sl: score=max(score,20)
            if score:
                hits.append({'score':score,'pointer':rec['pointer'],'record_id':rec['record_id'],'pack':rec['pack'],'summary':short(rec['record'])})
        hits.sort(key=lambda x:(-x['score'],x['pack'],x['record_id']))
        return hits[:limit]
    def expand(self,start_pointers,radius=1,max_results=50):
        frontier=set()
        for h in start_pointers:
            frontier.add(h['record_id']); frontier.add(h['pointer'])
        seen=set(); out=[]; depth=0
        while depth<int(radius) and len(out)<max_results:
            nxt=set()
            for rec in self.records:
                if rec['pointer'] in seen: continue
                strings=set(iter_strings(rec['record'])); strings.add(rec['record_id']); strings.add(rec['pointer'])
                if frontier.intersection(strings):
                    seen.add(rec['pointer'])
                    ids=sorted([s for s in strings if isinstance(s,str) and (s.startswith('SEED_') or s.startswith('BRIDGE_') or s.startswith('ROUTE_') or s.startswith('PATTERN_') or s.startswith('RESULTREC_'))])[:20]
                    out.append({'depth':depth+1,'pointer':rec['pointer'],'record_id':rec['record_id'],'pack':rec['pack'],'ids':ids,'summary':short(rec['record'])})
                    nxt.update(ids)
                    if len(out)>=max_results: break
            frontier=nxt
            if not frontier: break
            depth+=1
        return out
def load_memory(memory_root,pack_names=None):
    root=Path(memory_root); pack_names=pack_names or DEFAULT_PACKS; records=[]
    report={'memory_root':str(root),'packs_requested':pack_names,'packs_loaded':[],'packs_missing':[],'line_errors':[]}
    for pack in pack_names:
        p=find_pack(root,pack)
        if not p:
            report['packs_missing'].append(pack); continue
        count=0
        with p.open('r',encoding='utf-8-sig',errors='replace') as f:
            for i,line in enumerate(f,1):
                line=line.strip()
                if not line: continue
                try: obj=json.loads(line)
                except Exception as e:
                    report['line_errors'].append({'pack':pack,'line':i,'error':str(e)[:160]}); continue
                pointer=f'{pack}:{i}'; rid=record_id(obj,pointer)
                records.append({'pointer':pointer,'pack':pack,'line':i,'record_id':rid,'record':obj}); count+=1
        report['packs_loaded'].append({'pack':pack,'path':str(p),'records':count})
    return MemorySnapshot(root,records,report)
