"""Build into a new scene using datablocks, without clearing user content."""
import json
import math

import bmesh
import bpy
from mathutils import Vector


def _object(scene, name, data=None, location=(0, 0, 0)):
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = location
    return obj


def _shape(scene, name, location, scale, color, sphere=False, parent=None):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    if sphere:
        bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=1)
    else:
        bmesh.ops.create_cube(bm, size=2)
    bm.to_mesh(mesh)
    bm.free()
    obj = _object(scene, name, mesh, location)
    obj.scale = scale
    obj.parent = parent
    obj.color = (*color, 1)
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = obj.color
    obj.data.materials.append(mat)
    for polygon in mesh.polygons:
        polygon.use_smooth = sphere
    return obj


def _aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def _key(obj, path, value, frame):
    setattr(obj, path, value)
    obj.keyframe_insert(data_path=path, frame=frame)


def create_scene(plan):
    """Return a new editable studio. The caller controls activation and saving."""
    scene = bpy.data.scenes.new('M1 Studio')
    scene['screenwriter_m1'] = True
    scene['m1_plan'] = json.dumps(plan.to_dict(), ensure_ascii=False)
    scene.frame_start, scene.frame_end = 1, plan.frame_end
    scene.render.fps, scene.render.fps_base = plan.fps, 1
    scene.render.resolution_x, scene.render.resolution_y = 640, 360
    scene.render.resolution_percentage = 100
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.render.use_sequencer = False
    shading = scene.display.shading
    shading.light = 'STUDIO'
    shading.color_type = 'MATERIAL'
    shading.show_shadows = True
    shading.show_cavity = True
    shading.background_type = 'WORLD'
    scene.world = bpy.data.worlds.new('M1 World')
    scene.world.color = (0.06, 0.08, 0.12)
    _shape(scene, 'M1 Floor', (0, 0, -0.15), (7, 5, 0.15), (0.12, 0.17, 0.23))
    _shape(scene, 'M1 Backdrop', (0, 2.8, 2), (7, 0.12, 2.2), (0.08, 0.24, 0.3))
    _shape(scene, 'M1 Stage', (0, 0, 0.08), (3, 1.8, 0.08), (0.25, 0.29, 0.34))
    for x in (-3.5, 3.5):
        _shape(scene, 'M1 Set accent', (x, 2.5, 1.9), (0.09, 0.08, 1.6), (0.8, 0.55, 0.18))
    actors = {}
    colors = [(0.12, 0.55, 0.8), (0.95, 0.38, 0.13)]
    for i, name in enumerate(plan.characters):
        x = (-1.15, 1.15)[i]
        root = _object(scene, 'M1 Actor ' + name)
        root['character'] = name
        body = _shape(scene, name + ' torso', (0, 0, 1.15), (0.36, 0.23, 0.48), colors[i], True, root)
        head = _shape(scene, name + ' head', (0, 0, 1.95), (0.3, 0.27, 0.33), (0.78, 0.61, 0.43), True, root)
        for side in (-1, 1):
            _shape(scene, name + ' leg', (side * 0.19, 0, 0.46), (0.13, 0.16, 0.3), (0.08, 0.1, 0.16), False, root)
            _shape(scene, name + ' eye', (side * 0.10, -0.255, 2.02), (0.045, 0.025, 0.045), (0.02, 0.02, 0.02), True, root)
        arm = _shape(scene, name + ' gesture arm', (0.48, 0, 1.2), (0.12, 0.14, 0.4), colors[i], True, root)
        _shape(scene, name + ' resting arm', (-0.48, 0, 1.2), (0.12, 0.14, 0.4), colors[i], True, root)
        entrance_end = min(plan.beats[0].end - 1, 3 * plan.fps)
        _key(root, 'location', (x * 1.8, 0.4, 0.16), 1)
        _key(root, 'location', (x, 0, 0.16), entrance_end)
        _key(root, 'location', (x, 0, 0.16), plan.frame_end)
        actors[name] = (root, head, arm)
    cameras = {}
    for name, location, target, lens in [
        ('WIDE', (0, -9.5, 3.6), (0, 0, 1.25), 42),
        (plan.characters[0], (-2.4, -5.4, 2.6), (-1.15, 0, 1.45), 48),
        (plan.characters[1], (2.4, -5.4, 2.6), (1.15, 0, 1.45), 48),
    ]:
        cam = _object(scene, 'M1 Camera ' + name, bpy.data.cameras.new(name), location)
        cam.data.lens = lens
        _aim(cam, target)
        cam.keyframe_insert(data_path='location', frame=1)
        cam.location.y += 0.35
        cam.keyframe_insert(data_path='location', frame=plan.frame_end)
        cameras[name] = cam
    for index, beat in enumerate(plan.beats):
        marker = scene.timeline_markers.new(f'{index + 1:02} {beat.camera}', frame=beat.start)
        marker.camera = cameras[beat.camera]
        if beat.character:
            _, head, arm = actors[beat.character]
            # Neutral boundaries prevent interpolation across other speakers' beats.
            for frame, angle in [(1, 0), (beat.start, 0),
                                 ((beat.start + beat.end) // 2, 0.3), (beat.end - 1, 0),
                                 (plan.frame_end, 0)]:
                _key(arm, 'rotation_euler', (0, angle, 0), frame)
                _key(head, 'rotation_euler', (angle * 0.22, 0, 0), frame)
    for name, location, energy, size in [
        ('Key', (-3, -4, 6), 1200, 5), ('Fill', (4, -1, 4), 800, 4),
        ('Rim', (0, 2, 5), 1000, 3),
    ]:
        light = bpy.data.lights.new('M1 ' + name, 'AREA')
        light.energy, light.shape, light.size = energy, 'DISK', size
        obj = _object(scene, light.name, light, location)
        _aim(obj, (0, 0, 1))
    scene.camera = cameras[plan.beats[0].camera]
    scene.frame_set(1)
    return scene


def configure_movie(scene, filepath):
    if hasattr(scene.render.image_settings, 'media_type'):
        scene.render.image_settings.media_type = 'VIDEO'
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
    scene.render.filepath = str(filepath)


def subtitles(plan):
    def stamp(frame):
        ms = round((frame - 1) * 1000 / plan.fps)
        seconds, ms = divmod(ms, 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f'{hours:02}:{minutes:02}:{seconds:02},{ms:03}'
    entries = []
    for beat in plan.beats:
        if beat.kind == 'Dialogue':
            entries.append(f'{len(entries) + 1}\n{stamp(beat.start)} --> {stamp(beat.end)}\n{beat.character}: {beat.text}\n')
    return '\n'.join(entries)
