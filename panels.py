import bpy
from bpy_extras.io_utils import (
    ImportHelper,
    orientation_helper
    )

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


@orientation_helper(axis_forward='-Z', axis_up='Y')
class ImportSequence(bpy.types.Operator, ImportHelper):
    """Load a mesh sequence"""
    bl_idname = "ms.import_sequence"
    bl_label = "Import"
    bl_options = {'UNDO'}

    fileFormat: bpy.props.EnumProperty(
        items=[('obj', 'OBJ', 'Wavefront OBJ'),
               ('stl', 'STL', 'STereoLithography'),
               ('ply', 'PLY', 'Stanford PLY')],
        name='File Format',
        default='obj')

    obj_split_mode: bpy.props.EnumProperty(
        name="Split",
        items=(('ON', "Split", "Split geometry, omits unused verts"),
               ('OFF', "Keep Vert Order", "Keep vertex order from file")))
    
    stl_use_facet_normal: bpy.props.BoolProperty(
        name="Facet Normals",
        description="Use (import) facet normals (note that this will still give flat shading)",
        default=False
    )

    # TODO: we need all popular settings for OBJ, STL, and PLY represented here

    # material mode (one material total or one material per frame)
    perFrameMaterial: bpy.props.BoolProperty(
        name='Material per Frame',
        default=False)

    def execute(self, context):
        print("Imported a sequence")

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
        layout.row().prop(op, "fileFormat")

        if op.fileFormat == 'obj':
            layout.row().prop(op, "obj_split_mode")
        elif op.fileFormat == 'stl':
            layout.row().prop(op, "stl_use_facet_normal")
        # TODO: we need the rest of the OBJ, STL, and PLY settings here


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

        layout.prop(operator, "global_clight_size")
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
        layout.row().prop(op, "perFrameMaterial")


def menu_func_import_sequence(self, context):
    self.layout.operator(ImportSequence.bl_idname, text="Mesh Sequence")
