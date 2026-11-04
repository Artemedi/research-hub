"""Synthetic paths only; run with pinned Skill Doctor scripts on PYTHONPATH."""
from pathlib import Path
from collect_sessions import session_matches_repo

repo = Path('/projects/alpha')
cases = [('own_child', '/projects/alpha/src', True),
         ('unrelated_same_name', '/other/alpha/private', True),
         ('unrelated_other_name', '/other/beta/private', False)]
for name, cwd, expected in cases:
    actual = session_matches_repo(cwd, repo)
    print(f'{name}: {actual}')
    assert actual is expected
print('result: unrelated same-name path is accepted by fallback')
