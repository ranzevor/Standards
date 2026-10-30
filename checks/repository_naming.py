import sys
if sys.flags.optimize:
    raise RuntimeError('Validation requires assertions enabled; do not use -O or -OO')
"""Repository slug policy, not an instruction to rename remote repositories."""
import re
from datetime import date
SLUG=re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')
SUFFIX_ROLES={'sdk':'sdk','cli':'cli','mcp':'mcp-server','lib':'library','monorepo':'monorepo'}
STATUS={'temp','tmp','new','final','backup','archive','old','copy'}
def validate_name(name,*,style='PascalCase',kind='active',role='project',account=None,upstream=None,brand_slug=None,brand_basis=None,historical_name=None,historical_basis=None,suffix_reason=None):
 if type(name) is not str or not name:return False
 if kind=='organization-profile':return name in {'.github','.github-private'}
 if kind=='account-profile':return bool(account) and name==account
 if kind=='pages':return bool(account) and name==account+'.github.io'
 if kind=='upstream-fork':return bool(upstream) and name==upstream
 if kind=='historical-archive':
  return name==historical_name and type(historical_basis) is str and bool(historical_basis.strip()) and bool(re.fullmatch(r'[A-Za-z0-9_.-]+',name))
 if kind=='archive':
  m=re.fullmatch(r'(.+)-archive-(\d{4}-\d{2}-\d{2})',name)
  if not m:return False
  try:date.fromisoformat(m[2])
  except ValueError:return False
  return validate_name(m[1],style=style,role=role,brand_slug=brand_slug,brand_basis=brand_basis,suffix_reason=suffix_reason)
 patterns={'kebab-case':SLUG,'camelCase':re.compile(r'[a-z][A-Za-z0-9]*\Z'),'PascalCase':re.compile(r'[A-Z][A-Za-z0-9]*\Z')}
 if kind!='active' or style not in patterns:return False
 formal_brand=type(brand_basis) is str and bool(brand_basis.strip()) and bool(brand_slug) and name==brand_slug and bool(re.fullmatch(r'[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*',brand_slug))
 if formal_brand:return True # Record identity only; does not establish real brand rights.
 if not patterns[style].fullmatch(name):return False
 parts=name.split('-') if style=='kebab-case' else [p.lower() for p in re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)|[0-9]+',name)]
 if any(p in STATUS or re.fullmatch(r'v\d+(?:\.\d+)*|a\d{2,}|\d{8}|(?:19|20)\d{2}',p) for p in parts):return False
 if re.search(r'(?:V|v)\d+$|(?:A|a)\d{2,}$',name):return False
 if parts[-1] in {'repo','repository','project','test','dev'} and not suffix_reason:return False
 if parts[-1] in SUFFIX_ROLES and (role!=SUFFIX_ROLES[parts[-1]] or not suffix_reason):return False
 if style=='PascalCase' and not formal_brand:
  words=re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)|[0-9]+',name)
  if any(word.lower() in {'mcp','api','sdk','cli'} and word not in {'MCP','API','SDK','CLI'} for word in words):return False
 if brand_slug is not None:
  if not formal_brand and not patterns[style].fullmatch(brand_slug):return False
  if name!=brand_slug and not (name.startswith(brand_slug+('-' if style=='kebab-case' else '')) and suffix_reason):return False
 return True

def validate_selected_name(name,**kwargs):
    """Original repositories use PascalCase by default."""
    if 'style' in kwargs:raise ValueError('selected policy style is fixed')
    return validate_name(name,style='PascalCase',**kwargs)
