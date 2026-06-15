import re
from .bql_ast import make_ast
MAX_RADIUS=5
UNSAFE=['DELETE','UPDATE','INSERT','WRITE','WAL','EXEC','IMPORT',' OS ','SYSTEM','SUBPROCESS','__',';','|','&']
class ParseError(ValueError): pass
def _reject_unsafe(query):
    up=' '+query.upper()+' '
    for token in UNSAFE:
        if token in up: raise ParseError(f'unsafe token rejected: {token.strip()}')
def parse(query_text:str)->dict:
    if not isinstance(query_text,str) or not query_text.strip(): raise ParseError('empty query')
    q=' '.join(query_text.strip().split()); _reject_unsafe(q)
    explain=False
    if q.upper().startswith('EXPLAIN '): explain=True; q=q[8:].strip()
    m=re.match(r'^FROM\s+(seed|concept)\((?:"([^"]+)"|([A-Za-z0-9_:\-\.]+))\)\s+BALLOON\s+radius\s*=\s*(\d+)\s+direction\s*=\s*([a-zA-Z_]+)\s*(.*)$',q,flags=re.IGNORECASE)
    if not m: raise ParseError('unsupported BQL syntax')
    source_type=m.group(1); source_value=m.group(2) if m.group(2) is not None else m.group(3); radius=int(m.group(4)); direction=m.group(5).lower(); rest=m.group(6).strip()
    if radius<1 or radius>MAX_RADIUS: raise ParseError(f'radius out of bounds: {radius}; allowed 1..{MAX_RADIUS}')
    if direction not in {'up','down','up_down','lateral'}: raise ParseError(f'unsupported direction: {direction}')
    filters=[]
    if rest.upper().startswith('FILTER '):
        idx=rest.upper().find(' RETURN ')
        if idx<0: raise ParseError('FILTER requires RETURN')
        filter_text=rest[7:idx].strip(); ret=rest[idx+len(' RETURN '):].strip()
        fm=re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*"([^"]+)"$',filter_text)
        if not fm: raise ParseError('only simple equality filter is supported')
        filters.append({'field':fm.group(1),'op':'=','value':fm.group(2)})
    elif rest.upper().startswith('RETURN '): ret=rest[7:].strip()
    else: raise ParseError('RETURN clause required')
    if not ret: raise ParseError('RETURN requires fields')
    returns=[]
    for field in ret.split(','):
        f=field.strip()
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$',f): raise ParseError(f'invalid return field: {f}')
        returns.append(f)
    return make_ast(explain=explain,source_type=source_type.lower(),source_value=source_value,radius=radius,direction=direction,filters=filters,returns=returns)
