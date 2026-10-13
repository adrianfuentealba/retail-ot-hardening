import unittest,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('control_logic',ROOT/'plc/control_logic.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class RedTeamLogic(unittest.TestCase):
 def test_fc06_and_fc16_share_semantics(self):
  s=m.initial_state();self.assertTrue(m.apply_changes(s,[(0,50)])[0]);s['plc_guard']=True
  self.assertFalse(m.apply_changes(s,[(0,50)])[0]);self.assertTrue(m.apply_changes(s,[(0,3)])[0])
 def test_atomic_rejection(self):
  s=m.initial_state();self.assertFalse(m.apply_changes(s,[(0,50),(1,20)])[0]);self.assertEqual(s['setpoint'],2)
 def test_sensor_remote_guard(self):
  s=m.initial_state();self.assertTrue(m.apply_changes(s,[(4,800)])[0]);self.assertEqual(s['sensor_bias'],-20)
  s['input_guard']=True;self.assertFalse(m.apply_changes(s,[(4,800)])[0])
 def test_disconnected_unprotected_stops_cooling(self):
  s=m.initial_state();s['sensor_connected']=False;m.control_cycle(s);self.assertFalse(s['compressor']);self.assertFalse(s['sensor_valid'])
 def test_disconnected_protected_has_alarm_and_fallback(self):
  s=m.initial_state();s.update(sensor_connected=False,input_guard=True,temperature=10);m.control_cycle(s)
  self.assertTrue(s['fallback_active']);self.assertTrue(s['alarm']);self.assertTrue(s['compressor'])
 def test_sensor_bias_changes_same_physics(self):
  s=m.initial_state();m.apply_changes(s,[(4,800)]);m.control_cycle(s);self.assertFalse(s['compressor']);self.assertGreater(s['temperature'],2)
 def test_quarantine_not_rehabilitated(self):
  s=m.initial_state();s.update(temperature=20,exposure=12);m.control_cycle(s);s.update(temperature=2);m.control_cycle(s);self.assertTrue(s['spoiled'])
 def test_fixed_command_catalog(self):
  rows=json.loads((ROOT/'app/redteam-catalog.json').read_text());self.assertEqual(len(rows),6)
  code=(ROOT/'app/redteam.py').read_text();self.assertIn("('gateway',502)",code);self.assertIn('range(8)',code);self.assertNotIn('argparse',code)
 def test_no_learning_durations(self):
  import re
  for p in (ROOT/'exercises').glob('*.md'):self.assertIsNone(re.search(r'Duración:|\(\d+(?:[–-]\d+)? minutos?\)',p.read_text()))
if __name__=='__main__':unittest.main()
