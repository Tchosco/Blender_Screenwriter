"""Read a generated MP4 back through Blender and decode six review frames."""
import argparse
import json
from pathlib import Path
import sys
import bpy

parser = argparse.ArgumentParser()
parser.add_argument('directory', type=Path)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
output = args.directory.resolve()
report = json.loads((output / 'report.json').read_text(encoding='utf-8'))
assert report['render_mode'] == 'movie' and report['render_completed']
plan = report['plan']
clip = bpy.data.movieclips.load(str(output / 'movie.mp4'))
assert clip.frame_duration == plan['frame_end'], (clip.frame_duration, plan['frame_end'])
assert abs(clip.fps - plan['fps']) < 0.01
review = output / 'review'
review.mkdir(exist_ok=False)
scene = bpy.context.scene
scene.render.resolution_x, scene.render.resolution_y = clip.size
scene.render.resolution_percentage = 100
scene.render.fps = plan['fps']
scene.render.image_settings.file_format = 'PNG'
scene.render.use_sequencer = True
scene.sequence_editor_create().strips.new_movie('Verify MP4', str(output / 'movie.mp4'), channel=1, frame_start=1)
frames = [1, *[(b['start'] + b['end']) // 2 for b in plan['beats'][1:-1]], plan['frame_end']]
for frame in frames:
    scene.frame_set(frame)
    scene.render.filepath = str(review / f'decoded_{frame:04}.png')
    bpy.ops.render.render(write_still=True)
    assert Path(scene.render.filepath).stat().st_size > 100
result = {'decoded_review_frames': frames, 'frames': clip.frame_duration,
          'fps': clip.fps, 'seconds': clip.frame_duration / clip.fps,
          'size': list(clip.size), 'status': 'passed'}
(output / 'verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result))
