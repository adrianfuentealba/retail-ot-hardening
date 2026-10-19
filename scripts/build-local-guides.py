#!/usr/bin/env python3
"""Genera las guías noVNC desde Markdown. El HTML compilado se incluye en Git/Docker."""
from pathlib import Path
import hashlib,json,re,shutil,html
import markdown
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'workstation/guides';PAGES=OUT/'pages';SOURCES=OUT/'source'
RECOMMENDED={'00':'any','01':'ws-hmi','02':'ws-hmi','03':'ws-hmi','04':'ws-engineering','05':'ws-vendor','06':'ws-engineering','07':'ws-engineering','08':'ws-hmi','09':'ws-engineering','10':'ws-engineering'}
def main():
 PAGES.mkdir(parents=True,exist_ok=True);SOURCES.mkdir(exist_ok=True)
 sources=[ROOT/'docs/inicio-desde-novnc.md']+sorted((ROOT/'exercises').glob('*.md'))+sorted((ROOT/'docs').glob('*.md'))
 sources=list(dict.fromkeys(sources));mapping={p.resolve(): ('00' if p.name=='inicio-desde-novnc.md' else (p.name[:2] if p.parent.name=='exercises' and re.match(r'\d\d-',p.name) else ('solucion' if p.name=='solucion.md' else 'ref-'+p.stem))) for p in sources}
 manifest=[]
 for p in sources:
  text=p.read_text();slug=mapping[p.resolve()];title=text.splitlines()[0].lstrip('# ').strip()
  content=markdown.markdown(text,extensions=['fenced_code','tables','sane_lists','toc'],output_format='html5')
  def link(m):
   raw=m.group(1);parts=raw.split('#',1);target=(p.parent/parts[0]).resolve()
   if target in mapping:return 'href="index.html?guide='+html.escape(mapping[target],quote=True)+(('&anchor='+html.escape(parts[1],quote=True)) if len(parts)>1 else '')+'"'
   return m.group(0)
  content=re.sub(r'href="([^"\n]+)"',link,content)
  def image(m):
   target=(p.parent/m.group(1)).resolve()
   if target.is_file() and ROOT.resolve() in target.parents:
    dest=OUT/'media'/target.name;dest.parent.mkdir(exist_ok=True);shutil.copy2(target,dest);return 'src="media/'+html.escape(target.name,quote=True)+'"'
   return m.group(0)
  content=re.sub(r'src="([^"\n]+)"',image,content)
  (PAGES/(slug+'.html')).write_text(content+'\n');(SOURCES/(slug+'.md')).write_text(text)
  manifest.append({'id':slug,'title':title,'recommended':RECOMMENDED.get(slug,'reference'),'file':'pages/'+slug+'.html','source':'source/'+slug+'.md','sha256':hashlib.sha256(text.encode()).hexdigest(),'upstream':str(p.relative_to(ROOT))})
 # Remove obsolete generated pages, but preserve UI assets.
 for folder,ext in [(PAGES,'.html'),(SOURCES,'.md')]:
  for p in folder.glob('*'+ext):
   if p.stem not in {x['id'] for x in manifest}:p.unlink()
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print(f'Guías compiladas: {len(manifest)}; talleres: {sum(x["id"] in [f"{i:02d}" for i in range(1,11)] for x in manifest)}')
if __name__=='__main__':main()
