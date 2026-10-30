import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fountain import Fountain
from m1.plan import build_plan

SAMPLE = (Path(__file__).resolve().parents[1] / 'examples/m1_studio.fountain').read_text(encoding='utf-8')


class ParserTests(unittest.TestCase):
    def test_empty(self):
        for text in ('', '  \n', None):
            self.assertEqual(Fountain(text).elements, [])

    def test_metadata_continuation_and_malformed_line(self):
        f = Fountain('Title: Test\n  continued\nmalformed\nAuthor: Ana\n\nINT. ROOM - DAY\n\nAction.')
        self.assertEqual(f.metadata['title'], ['Test', 'continued'])
        self.assertEqual(f.metadata['author'], ['Ana'])
        self.assertTrue(any(e.element_type == 'Scene Heading' for e in f.elements))

    def test_multiline_action_not_character(self):
        f = Fountain('INT. ROOM - DAY\n\nAna enters.\nShe waits.\n\nANA\nHello.')
        self.assertEqual([e.element_text for e in f.elements if e.element_type == 'Character'], ['ANA'])
        self.assertEqual([e.element_text for e in f.elements if e.element_type == 'Action'], ['Ana enters.\nShe waits.'])

    def test_forced_character(self):
        f = Fountain('INT. ROOM - DAY\n\n@Ana\nHello.')
        self.assertIn('Ana', [e.element_text for e in f.elements if e.element_type == 'Character'])


class PlanTests(unittest.TestCase):
    def test_contiguous_exact_duration(self):
        for duration, fps in [(30, 12), (40, 24), (60, 30)]:
            plan = build_plan(SAMPLE, duration, fps)
            self.assertEqual(plan.characters, ('ANA', 'BRUNO'))
            self.assertEqual(plan.frame_end, duration * fps)
            self.assertEqual(plan.beats[0].start, 1)
            self.assertEqual(plan.beats[-1].end, plan.frame_end + 1)
            for left, right in zip(plan.beats, plan.beats[1:]):
                self.assertEqual(left.end, right.start)
            self.assertTrue(all(b.end - b.start >= fps for b in plan.beats))
            self.assertEqual(plan, build_plan(SAMPLE, duration, fps))

    def test_shots(self):
        plan = build_plan(SAMPLE)
        self.assertEqual([b.camera for b in plan.beats], ['WIDE', 'ANA', 'BRUNO', 'ANA', 'BRUNO', 'WIDE'])
        with self.assertRaisesRegex(ValueError, 'Unknown SHOT'):
            build_plan(SAMPLE.replace('SHOT: WIDE', 'SHOT: MISSING', 1))

    def test_invalid_inputs(self):
        for text in ['', SAMPLE.replace('BRUNO\n', 'ANA\n'), SAMPLE + '\n\nEXT. ROAD - DAY\n', SAMPLE + '\n\n[[SHOT: WIDE]]']:
            with self.assertRaises(ValueError):
                build_plan(text)
        for duration in [29, 61, float('nan')]:
            with self.assertRaises(ValueError):
                build_plan(SAMPLE, duration)


if __name__ == '__main__':
    unittest.main()
