"""Integration assertions, run inside Blender with --python-exit-code 1."""
from pathlib import Path
import importlib
import sys
import bpy

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root.parent))
addon = importlib.import_module(root.name)
addon.register()
assert hasattr(bpy.types.Scene, 'keywords_assigner')
assert hasattr(bpy.ops.screenwriter, 'generate_m1')
from Blender_Screenwriter.m1.plan import build_plan
from Blender_Screenwriter.m1.scene import create_scene, subtitles, configure_movie
from Blender_Screenwriter.operators.scene_to_strip import to_scenes

script = (root / 'examples/m1_studio.fountain').read_text(encoding='utf-8')
legacy = to_scenes(script)
assert len(legacy) == 1
assert len([b for b in legacy[0].elements if type(b).__name__ == 'Dialogue']) == 4
original = bpy.context.scene
original_objects = tuple(original.objects)
plan = build_plan(script)
scene = create_scene(plan)
second = create_scene(plan)
assert scene != second
assert bpy.context.scene == original
assert tuple(original.objects) == original_objects
assert scene.frame_end == 960 and scene.render.fps == 24
assert len([o for o in scene.objects if 'character' in o]) == 2
assert len([o for o in scene.objects if o.type == 'CAMERA']) == 3
assert len(scene.timeline_markers) == len(plan.beats)
for beat in plan.beats:
    scene.frame_set(beat.start)
    assert scene.camera.name.startswith('M1 Camera ' + beat.camera)
actor = next(o for o in scene.objects if o.get('character') == 'ANA')
bpy.context.window.scene = scene
scene.frame_set(1)
start = actor.location.copy()
scene.frame_set(100)
assert (actor.location - start).length > 0.1
assert 'ANA:' in subtitles(plan) and 'BRUNO:' in subtitles(plan)
configure_movie(scene, '/tmp/m1-test.mp4')
assert scene.render.is_movie_format
assert scene.render.ffmpeg.codec == 'H264'
# Exercise both visible operators with a real Text Editor context.
bpy.context.window.scene = original
area = bpy.context.screen.areas[0]
area.type = 'TEXT_EDITOR'
text = bpy.data.texts.new('m1_test.fountain')
text.write(script)
area.spaces.active.text = text
with bpy.context.temp_override(area=area):
    assert bpy.ops.screenwriter.generate_m1(duration=30) == {'FINISHED'}
    assert bpy.context.scene.frame_end == 720
    bpy.context.window.scene = original
    assert bpy.ops.screenwriter.fountain_to_strips() == {'FINISHED'}
    assert len(original.sequence_editor.strips) > 0
addon.unregister()
addon.register()
addon.unregister()
print('M1 BLENDER SMOKE PASSED: registration, legacy adapter, preservation, cameras, motion, subtitles')
