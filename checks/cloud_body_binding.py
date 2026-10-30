"""Full Markdown block binding with bounded formatting equivalence."""
import sys
if sys.flags.optimize:
    raise RuntimeError('optimized validation (-O/-OO) is unsupported')
import re

def cjk(ch):return bool(ch) and ('\u3400'<=ch<='\u9fff' or '\uf900'<=ch<='\ufaff')
def soft_join(lines):
 out=''
 for line in lines:
  line=line.strip()
  if not line:continue
  if out:
   # Only join CJK-to-CJK soft wraps without a new word separator.
   out+=('' if cjk(out[-1]) and cjk(line[0]) else ' ')+line
  else:out=line
 return out

def normalize_paragraph(text):return soft_join(text.strip().splitlines())
def blocks(text):
 result=[]
 for block in re.split(r'\n[ \t]*\n+',text.strip()):
  lines=[l.rstrip() for l in block.splitlines() if l.strip()]
  if not lines:continue
  # Heading/anchor and table line structure carries Markdown semantics.
  if any(l.startswith(('#','|','<a ')) for l in lines):result.append('\n'.join(l.strip() for l in lines))
  else:result.append(soft_join(lines))
 return result
