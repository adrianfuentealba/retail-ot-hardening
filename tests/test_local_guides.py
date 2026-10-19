import ast,hashlib,json,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BUNDLE=ROOT/'workstation/guides'
class LocalGuides(unittest.TestCase):
 def setUp(self):self.manifest=json.loads((BUNDLE/'manifest.json').read_text())
 def test_all_ten_workshops_and_start(self):
  self.assertTrue({f'{i:02d}' for i in range(11)}.issubset({x['id'] for x in self.manifest}))
  self.assertIn('solucion',{x['id'] for x in self.manifest})
 def test_sources_and_pages_match(self):
  for row in self.manifest:
   text=(ROOT/row['upstream']).read_text();self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),row['sha256'])
   self.assertEqual(text,(BUNDLE/row['source']).read_text());self.assertGreater((BUNDLE/row['file']).stat().st_size,500)
 def test_no_remote_assets_or_autoexecute(self):
  html=(BUNDLE/'index.html').read_text();js=(BUNDLE/'guides.js').read_text()
  self.assertNotRegex(html,r'(src|href)="https?://')
  self.assertNotIn("method:'POST'",js);self.assertNotIn('eval(',js);self.assertIn('clipboard.writeText',js)
  self.assertIn('NO EJECUTAR',js);self.assertIn('Ctrl + Shift + V',js)
 def test_routes_and_desktop_launch(self):
  source=(ROOT/'workstation/agent.py').read_text();start=(ROOT/'workstation/start.sh').read_text();docker=(ROOT/'workstation/Dockerfile').read_text()
  self.assertIn("app.mount('/guides'",source);self.assertIn('Guias.desktop',start);self.assertIn('http://127.0.0.1:8010/guides/',start);self.assertIn('COPY guides /opt/retail/guides',docker)
 def test_cli_scope_preserved(self):
  source=(ROOT/'workstation/agent.py').read_text();cli=(ROOT/'workstation/labctl.py').read_text()
  self.assertIn("if c=='reset':",source);self.assertIn("['classroom-state','reset-all']",source);self.assertIn('TODA el aula',cli)
  self.assertNotIn('shell=True',cli);self.assertIn("'http://panel:8000/api/reset'",source)
 def test_all_workshops_have_expected_and_diagnosis(self):
  for i in range(1,11):
   p=next((ROOT/'exercises').glob(f'{i:02d}-*.md'));text=p.read_text().lower()
   self.assertGreaterEqual(text.count('resultado esperado'),3,str(p))
   self.assertTrue(any(s in text for s in ['si no','si el','si obtienes','si aparece','si sale']),str(p))
   self.assertIn('novnc',text);self.assertNotRegex(text,r'\b(?:duración|tiempo estimado)\s*:')
 def test_guide_commands_are_in_cli(self):
  tree=ast.parse((ROOT/'workstation/labctl.py').read_text());allowed=[]
  for node in tree.body:
   if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='allowed' for t in node.targets):allowed.extend(ast.literal_eval(node.value))
   if isinstance(node,ast.AugAssign) and isinstance(node.target,ast.Name) and node.target.id=='allowed':allowed.extend(ast.literal_eval(node.value))
  for p in (ROOT/'exercises').glob('[0-9][0-9]-*.md'):
   for block in re.findall(r'```(?:bash|sh|shell)\n(.*?)```',p.read_text(),re.S):
    for line in block.splitlines():
     if line.strip().startswith('labctl '):
      command=line.strip()[7:].split('|')[0].split('>')[0].strip()
      if command.startswith('guides'):continue
      self.assertIn(command,allowed,(p.name,line))
if __name__=='__main__':unittest.main()
