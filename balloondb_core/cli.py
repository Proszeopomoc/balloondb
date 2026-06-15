import argparse,json,sys
from .bql_parser import parse,ParseError
from .bql_planner import explain as make_plan
from .role_map_loader import load_role_map
def _read_query(args):
    if getattr(args,'query_file',None):
        with open(args.query_file,'r',encoding='utf-8-sig') as f: return f.read().strip()
    return args.query
def cmd_parse(args): print(json.dumps(parse(_read_query(args)),ensure_ascii=False,indent=2)); return 0
def cmd_explain(args):
    ast=parse(_read_query(args)); print(json.dumps({'ast':ast,'plan':make_plan(ast)},ensure_ascii=False,indent=2)); return 0
def cmd_query(args):
    from .bql_executor import execute
    result=execute(_read_query(args),memory_root=args.memory_root,max_results=args.max_results)
    print(json.dumps(result,ensure_ascii=False,indent=2)); return 0 if result['status'].startswith('PASS') else 4
def cmd_validate_scripts(args):
    result=load_role_map(args.role_map); print(json.dumps(result,ensure_ascii=False,indent=2)); return 0 if result.get('ok') else 2
def cmd_selftest(args):
    from .selftest.run_selftest import run_selftest
    result=run_selftest(); print(json.dumps(result,ensure_ascii=False,indent=2)); return 0 if result.get('status')=='PASS_V03G0_BQL_SELFTEST' else 3
def cmd_selftest_v03g1(args):
    from .selftest.run_selftest_v03g1 import run_selftest
    result=run_selftest(args.memory_root); print(json.dumps(result,ensure_ascii=False,indent=2)); return 0 if result.get('status')=='PASS_V03G1_BQL_SELFTEST' else 5
def _query_args(p): p.add_argument('--query',required=False,default=''); p.add_argument('--query-file',required=False)
def main(argv=None):
    ap=argparse.ArgumentParser(prog='balloondb-bql',description='BalloonDB BQL'); sub=ap.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('parse'); _query_args(p); p.set_defaults(fn=cmd_parse)
    p=sub.add_parser('explain'); _query_args(p); p.set_defaults(fn=cmd_explain)
    p=sub.add_parser('query'); _query_args(p); p.add_argument('--memory-root',default=r'C:\BalloonOperator\memory\balloon_memory.balloondb'); p.add_argument('--max-results',type=int,default=50); p.set_defaults(fn=cmd_query)
    p=sub.add_parser('validate-scripts'); p.add_argument('--role-map',default=r'C:\BalloonOperator\config\BALLOONDB_V03G0_SCRIPT_ROLE_MAP.json'); p.set_defaults(fn=cmd_validate_scripts)
    p=sub.add_parser('selftest'); p.set_defaults(fn=cmd_selftest)
    p=sub.add_parser('selftest-v03g1'); p.add_argument('--memory-root',default=r'C:\BalloonOperator\memory\balloon_memory.balloondb'); p.set_defaults(fn=cmd_selftest_v03g1)
    args=ap.parse_args(argv)
    try: return args.fn(args)
    except ParseError as e:
        print(json.dumps({'status':'BQL_PARSE_ERROR','error':str(e)},ensure_ascii=False),file=sys.stderr); return 2
if __name__=='__main__': raise SystemExit(main())
