from pathlib import Path
import hashlib,json,re,sys
if sys.flags.optimize:raise RuntimeError("optimized validation (-O/-OO) is unsupported")
ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/'standards/L4/cloud'
DOCUMENT_NUMBERS={'BL':3,'IAM':5,'NET':4,'ISO':2,'IAC':7,'CI':1,'SUP':11,
                  'SEC':13,'REL':6,'CAP':9,'OBS':12,'DR':8,'COST':10}
def document_names(root=ROOT):
 rows=json.loads((Path(root)/'registry/standards.json').read_text('utf-8'))
 selected={row['id']:row for row in rows if row['domain']=='cloud'}
 if len(selected)!=13:raise ValueError('cloud current registry coverage')
 result={}
 for code,number in DOCUMENT_NUMBERS.items():
  entry=selected[f'STD-L4-CLOUD-{number:03d}'];path=Path(entry['path'])
  if path.parent.as_posix()!='standards/L4/cloud':raise ValueError('cloud document path outside domain')
  result[code]=path.name
 return result
DOCS=document_names()
def digest(b):return hashlib.sha256(b).hexdigest()
def parse_document(path):
 text=path.read_text()
 pattern=r'^### §(\d{2}) ([^\n]+)\n\*\*机制：\*\* (.+?)\n\n\*\*验收：\*\* (.+?)(?=\n\n|\Z)'
 clauses=[]
 for m in re.finditer(pattern,text,re.M|re.S):
  n,title,mechanism,acceptance=m.groups();clauses.append(dict(number=int(n),title=title,mechanism=mechanism,acceptance=acceptance,original_section=m.group(0)))
 cases=[]
 for line in text.splitlines():
  if line.startswith('|'):
   cells=[x.strip() for x in line.strip('|').split('|')]
   if len(cells)==3 and re.fullmatch(r'§\d{2}(?:、§\d{2})*',cells[1]):
    cases.append(dict(input=cells[0],clauses=[int(x) for x in re.findall(r'\d{2}',cells[1])],expected=cells[2]))
 return dict(text=text,clauses=clauses,cases=cases)
if __name__=='__main__':
 for code,name in DOCS.items():
  d=parse_document(INPUT/name);print(code,len(d['clauses']),len(d['cases']))
