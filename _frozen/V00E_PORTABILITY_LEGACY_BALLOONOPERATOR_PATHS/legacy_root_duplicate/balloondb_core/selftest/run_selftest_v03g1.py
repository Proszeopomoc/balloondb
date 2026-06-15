import json,html,time
from pathlib import Path
from balloondb_core.bql_executor import execute
ROOT=Path(r'C:\BalloonOperator'); CORE=ROOT/'balloondb_core'
def run_selftest(memory_root):
    data_dir=CORE/'data'; report_dir=CORE/'reports'; data_dir.mkdir(parents=True,exist_ok=True); report_dir.mkdir(parents=True,exist_ok=True)
    query='FROM seed("PASS_V03G0_BQL_SELFTEST") BALLOON radius=2 direction=up_down RETURN route,evidence,concept'
    result=execute(query,memory_root=memory_root,max_results=30)
    out_path=data_dir/'v03g1_selftest_output.jsonl'; out_path.write_text(json.dumps(result,ensure_ascii=False)+'\n',encoding='utf-8')
    status='PASS_V03G1_BQL_SELFTEST' if result['status'].startswith('PASS') else 'FAIL_V03G1_BQL_SELFTEST'
    report_path=report_dir/'v03g1_selftest_report.html'
    report_path.write_text('<!doctype html><meta charset="utf-8"><h1>'+html.escape(status)+'</h1><p>seed_match_count='+str(result['seed_lookup']['match_count'])+'</p><p>expand_result_count='+str(result['balloon_expand']['result_count'])+'</p><pre>'+html.escape(json.dumps(result['safety'],ensure_ascii=False,indent=2))+'</pre>',encoding='utf-8')
    return {'status':status,'version':'V03G1_BQL_SEED_LOOKUP_AND_BALLOON_EXPAND_V0','query':query,'seed_match_count':result['seed_lookup']['match_count'],'expand_result_count':result['balloon_expand']['result_count'],'output':str(out_path),'report':str(report_path),'ts':int(time.time()*1000)}
