import importlib.util, sys, types, re, sqlite3
for name in ('hyperresearch','hyperresearch.core','hyperresearch.core.fetcher','hyperresearch.core.patterns','hyperresearch.core.scholar'):
    mod=types.ModuleType(name); mod.__path__=[]; sys.modules[name]=mod
sys.modules['hyperresearch.core.fetcher'].existing_live_note_for_url=lambda *a: None
sys.modules['hyperresearch.core.patterns'].WIKI_LINK_RE=re.compile(r'\[\[([^\]\[|]+)(?:\|[^\]\[]+)?\]\](?!\()')
sys.modules['hyperresearch.core.patterns'].mask_code=lambda x:x
sys.modules['hyperresearch.core.scholar'].DOI_RE=re.compile('nevermatching')
sys.modules['hyperresearch.core.scholar'].extract_doi=lambda x:None
spec=importlib.util.spec_from_file_location('hyperresearch.core.citecheck','/source/src/hyperresearch/core/citecheck.py')
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
conn=sqlite3.connect(':memory:'); conn.row_factory=sqlite3.Row
conn.execute('create table claims(note_id text, claim text, quoted_support text, numbers text)')
conn.execute('insert into claims values(?,?,?,?)',('s','The vaccine is safe for all adults and children','',''))
def triage(sentence):
    return module.triage_pairs([dict(note_id='s',sentence=sentence,marker='[[s]]',numbers=[],strong=False)],conn)['pairs'][0]['verdict']
for s in ['The vaccine is safe for all adults and children [[s]].','The vaccine is safe for all adults but not children [[s]].','An unrelated topic is considered by an independent expert [[s]].']:
    print(repr(s),triage(s))
assert triage('The vaccine is safe for all adults but not children [[s]].')=='supported-mechanical'
assert triage('An unrelated topic is considered by an independent expert [[s]].')=='needs-llm'
