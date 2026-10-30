"""blender -b --factory-startup --python-exit-code 1 --python scripts/m1_build.py -- ..."""
import argparse
import json
from pathlib import Path
import sys

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from m1.plan import build_plan
from m1.scene import configure_movie, create_scene, subtitles


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--script', type=Path, default=ROOT / 'examples/m1_studio.fountain')
    parser.add_argument('--output', type=Path, required=True,
                        help='New directory; existing directories are never overwritten')
    parser.add_argument('--duration', type=int, default=40)
    parser.add_argument('--fps', type=int, default=24)
    parser.add_argument('--width', type=int, default=640)
    parser.add_argument('--render', choices=['none', 'stills', 'movie'], default='none')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    if not 160 <= args.width <= 3840:
        parser.error('--width must be 160..3840')
    plan = build_plan(args.script.read_text(encoding='utf-8-sig'), args.duration, args.fps)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = {'blender': bpy.app.version_string, 'build_hash': bpy.app.build_hash.decode(),
              'status': 'started', 'render_mode': args.render, 'render_completed': False,
              'plan': plan.to_dict()}
    report_path = output / 'report.json'
    def save_report():
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    save_report()
    try:
        scene = create_scene(plan)
        bpy.context.window.scene = scene
        scene.render.resolution_x = args.width
        scene.render.resolution_y = round(args.width * 9 / 16 / 2) * 2
        (output / 'movie.srt').write_text(subtitles(plan), encoding='utf-8')
        (output / 'source.fountain').write_text(args.script.read_text(encoding='utf-8-sig'), encoding='utf-8')
        configure_movie(scene, output / 'movie.mp4')
        bpy.ops.wm.save_as_mainfile(filepath=str(output / 'studio.blend'))
        report['scene'] = scene.name
        report['objects'] = len(scene.objects)
        if args.render == 'movie':
            bpy.ops.render.render(animation=True, scene=scene.name)
            movie = output / 'movie.mp4'
            if not movie.exists() or movie.stat().st_size < 1024:
                raise RuntimeError('Renderer returned without a usable movie file')
            report['movie_bytes'] = movie.stat().st_size
            report['render_completed'] = True
        elif args.render == 'stills':
            if hasattr(scene.render.image_settings, 'media_type'):
                scene.render.image_settings.media_type = 'IMAGE'
            scene.render.image_settings.file_format = 'PNG'
            frames = sorted({b.start for b in plan.beats} | {plan.frame_end})
            for frame in frames:
                scene.frame_set(frame)
                scene.render.filepath = str(output / f'frame_{frame:04}.png')
                bpy.ops.render.render(write_still=True, scene=scene.name)
            report['rendered_frames'] = frames
            report['render_completed'] = True
        report['status'] = 'passed'
    except Exception as exc:
        report['status'] = 'failed'
        report['error'] = str(exc)
        raise
    finally:
        save_report()


if __name__ == '__main__':
    main()
