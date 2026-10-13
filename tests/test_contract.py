import unittest,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Contract(unittest.TestCase):
 def test_loopback_only(self):
  c=json.loads((ROOT/'docker-compose.yml').read_text())
  for s in c['services'].values():
   for p in s.get('ports',[]):self.assertTrue(p.startswith('127.0.0.1:'))
  self.assertEqual(len([x for x in c['services'] if x.startswith('ws-')]),5)
 def test_guides(self):
  for n in range(1,11):self.assertTrue(list((ROOT/'exercises').glob(f'{n:02d}-*.md')))
 def test_no_socket(self):self.assertNotIn('docker.sock',(ROOT/'docker-compose.yml').read_text())
 def test_protocol_ports_not_published(self):
  c=json.loads((ROOT/'docker-compose.yml').read_text())
  for s in c['services'].values():self.assertFalse(any(p.endswith(':502') or p.endswith(':4840') for p in s.get('ports',[])))
if __name__=='__main__':unittest.main()
