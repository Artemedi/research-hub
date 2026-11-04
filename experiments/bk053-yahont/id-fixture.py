"""Exercise only the pinned pure ID filtering helper on synthetic strings."""
import importlib.util
import sys
spec = importlib.util.spec_from_file_location('yahont_id_filter', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
f = module.filter_and_validate_document_id
assert f('a/b') == f('ab') == 'ab'
assert f('doc_1') == 'doc_1'
try:
    f('///')
except ValueError:
    pass
else:
    raise AssertionError('empty normalized ID must be rejected')
print('a/b ->', f('a/b'), '; ab ->', f('ab'), '; doc_1 ->', f('doc_1'))
