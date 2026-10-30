import bpy
from bpy.props import IntProperty
from ..m1.plan import build_plan
from ..m1.scene import create_scene


class SCREENWRITER_OT_generate_m1(bpy.types.Operator):
    """Create a new studio scene from the active Fountain text (two speakers)"""
    bl_idname = 'screenwriter.generate_m1'
    bl_label = 'Generate M1 3D'
    bl_options = {'REGISTER', 'UNDO'}

    duration: IntProperty(name='Duration (seconds)', default=40, min=30, max=60)

    @classmethod
    def poll(cls, context):
        return (context.area is not None and context.area.type == 'TEXT_EDITOR'
                and context.space_data.text is not None)

    def execute(self, context):
        try:
            plan = build_plan(context.space_data.text.as_string(), self.duration)
        except ValueError as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        scene = create_scene(plan)
        context.window.scene = scene
        self.report({'INFO'}, f'{scene.name}: {self.duration}s, 2 actors, 3 cameras. Save as a new .blend.')
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
