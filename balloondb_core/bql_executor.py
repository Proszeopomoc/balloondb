from .bql_parser import parse, ParseError
from .bql_memory_reader import load_memory
MAX_EXEC_RADIUS=3
def execute(query_text,memory_root,max_results=50):
    ast=parse(query_text); radius=int(ast['balloon']['radius'])
    if radius<1 or radius>MAX_EXEC_RADIUS: raise ParseError(f'executor radius out of bounds: {radius}; allowed 1..{MAX_EXEC_RADIUS}')
    snap=load_memory(memory_root); seed_value=ast['source']['value']
    matches=snap.find_seed(seed_value,limit=10)
    expanded=snap.expand(matches,radius=radius,max_results=max_results) if matches else []
    return {'status':'PASS_V03G1_BQL_QUERY_EXECUTED' if matches else 'WARN_V03G1_SEED_NOT_FOUND','version':'V03G1_BQL_SEED_LOOKUP_AND_BALLOON_EXPAND_V0','read_only':True,'query':query_text,'ast':ast,'memory_report':snap.load_report,'seed_lookup':{'seed':seed_value,'match_count':len(matches),'matches':matches},'balloon_expand':{'radius':radius,'direction':ast['balloon']['direction'],'result_count':len(expanded),'results':expanded},'safety':{'no_write':True,'no_wal':True,'no_vector_engine':True,'no_full_graph_export':True,'max_radius':MAX_EXEC_RADIUS,'max_results':max_results}}
