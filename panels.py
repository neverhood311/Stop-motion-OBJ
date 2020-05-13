import bpy
from bpy_extras.io_utils import (
    ImportHelper,
    orientation_helper
    )

from .stop_motion_obj import MeshSequenceSettings

# The properties panel added to the Object Properties Panel list
class MeshSequencePanel(bpy.types.Panel):
    bl_idname = 'OBJ_SEQUENCE_PT_properties'
    bl_label = 'Mesh Sequence'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'

    @classmethod
    def poll(cls, context):
        return context.object.mesh_sequence_settings.initialized == True

    def draw(self, context):
        layout = self.layout
        objSettings = context.object.mesh_sequence_settings
        if objSettings.initialized is True:
            # Only show options for loading a sequence if one hasn't been loaded yet
            if objSettings.loaded is False:
                layout.label(text="Load Mesh Sequence:", icon='FILE_FOLDER')
                row = layout.row()
                row.prop(objSettings, "dirPath")

                row = layout.row()
                row.prop(objSettings, "fileName")

                row = layout.row()
                row.prop(objSettings, "fileFormat")

                row = layout.row()
                row.prop(objSettings, "perFrameMaterial")

                row = layout.row()
                row.prop(objSettings, "cacheMode")

                row = layout.row()
                row.operator("ms.load_mesh_sequence")

            if objSettings.loaded is True:
                row = layout.row()
                row.prop(objSettings, "startFrame")

                row = layout.row()
                row.prop(objSettings, "frameMode")

                row = layout.row()
                row.prop(objSettings, "speed")

                if objSettings.cacheMode == 'cached':
                    row = layout.row()
                    row.operator("ms.reload_mesh_sequence")

                    layout.row().separator()
                    row = layout.row(align=True)
                    row.label(text="Shading:")
                    row.operator("ms.batch_shade_smooth")
                    row.operator("ms.batch_shade_flat")

                    layout.row().separator()
                    row = layout.row()
                    box = row.box()
                    box.operator("ms.bake_sequence")

                elif objSettings.cacheMode == 'streaming':
                    row = layout.row()
                    row.prop(objSettings, "cacheSize")

                    row = layout.row()
                    row.prop(objSettings, "streamDuringPlayback")


class OBJImportSettings(bpy.types.PropertyGroup):
    use_edges: bpy.props.BoolProperty(name="Lines", description="Import lines and faces with 2 verts as edge", default=True)
    use_smooth_groups: bpy.props.BoolProperty(name="Smooth Groups", description="Surround smooth groups by sharp edges", default=True)
    use_split_objects: bpy.props.BoolProperty(name="Object", description="Import OBJ Objects into Blender Objects", default=True)
    use_split_groups: bpy.props.BoolProperty(name="Group", description="Import OBJ Groups into Blender Objects", default=False)
    use_groups_as_vgroups: bpy.props.BoolProperty(name="Poly Groups", description="Import OBJ groups as vertex groups", default=False)
    use_image_search: bpy.props.BoolProperty(name="Image Search", description="Search subdirs for any associated images (Warning: may be slow)", default=True)
    split_mode: bpy.props.EnumProperty(
        name="Split",
        items=(('ON', "Split", "Split geometry, omits unused vertices"),
               ('OFF', "Keep Vert Order", "Keep vertex order from file")))
    global_clight_size: bpy.props.FloatProperty(
        name="Clamp Size",
        description="Clamp bounds under this value (zero to disable)",
        min=0.0,
        max=1000.0,
        soft_min=0.0,
        soft_max=1000.0,
        default=0.0)


class STLImportSettings(bpy.types.PropertyGroup):
    global_scale: bpy.props.FloatProperty(
        name="Scale",
        soft_min=0.001,
        soft_max=1000.0,
        min=1e-6,
        max=1e6,
        default=1.0)
    use_scene_unit: bpy.props.BoolProperty(
        name="Scene Unit",
        description="Apply current scene's unit (as defined by unit scale) to imported data",
        default=False)
    use_facet_normal: bpy.props.BoolProperty(
        name="Facet Normals",
        description="Use (import) facet normals (note that this will still give flat shading)",
        default=False)


@orientation_helper(axis_forward='-Z', axis_up='Y')
class ImportSequence(bpy.types.Operator, ImportHelper):
    """Load a mesh sequence"""
    bl_idname = "ms.import_sequence"
    bl_label = "Import"
    bl_options = {'UNDO'}

    objSettings: bpy.props.PointerProperty(type=OBJImportSettings)
    stlSettings: bpy.props.PointerProperty(type=STLImportSettings)
    mss: bpy.props.PointerProperty(type=MeshSequenceSettings)

    def execute(self, context):
        print("Imported a sequence")
        # TODO:
        # the input parameters should be stored on 'self'
        # create a new mesh sequence
        # load the mesh sequence
        # (basically what's happening in the LoadMeshSequence operator)
        # TODO: return {'FINISHED'}

    # we need this function so it doesn't try to render any UI elements. The ImportSequencePanel will do all the drawing
    def draw(self, context):
        pass


class FileImportSettingsPanel(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "File Settings"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "MS_OT_import_sequence"

    def draw(self, context):
        op = context.space_data.active_operator
        layout = self.layout
        layout.row().prop(op.mss, "fileFormat")

        if op.mss.fileFormat == 'obj':
            layout.prop(op.objSettings, 'use_image_search')
            layout.prop(op.objSettings, 'use_smooth_groups')
            layout.prop(op.objSettings, 'use_edges')
            layout.prop(op.objSettings, 'global_clight_size')
            layout.prop(op.objSettings, 'split_mode')

            col = layout.column()
            if op.objSettings.split_mode == 'ON':
                col.prop(op.objSettings, "use_split_objects", text="Split by Object")
                col.prop(op.objSettings, "use_split_groups", text="Split by Group")
            else:
                col.prop(op.objSettings, "use_groups_as_vgroups")

        elif op.mss.fileFormat == 'stl':
            layout.row().prop(op.stlSettings, "global_scale")
            layout.row().prop(op.stlSettings, "use_scene_unit")
            layout.row().prop(op.stlSettings, "use_facet_normal")
        elif op.mss.fileFormat == 'ply':
            layout.label(text="No .ply settings")


class TransformSettingsPanel(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Transform"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        return context.space_data.active_operator.bl_idname == "MS_OT_import_sequence"
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "axis_forward")
        layout.prop(operator, "axis_up")


class SequenceImportSettingsPanel(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Sequence Settings"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        return context.space_data.active_operator.bl_idname == "MS_OT_import_sequence"
    
    def draw(self, context):
        op = context.space_data.active_operator
        layout = self.layout
        layout.row().prop(op.mss, "fileName")
        layout.row().prop(op.mss, "perFrameMaterial")
        layout.row().prop(op.mss, "cacheMode")


def menu_func_import_sequence(self, context):
    self.layout.operator(ImportSequence.bl_idname, text="Mesh Sequence")
