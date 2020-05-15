import bpy
from bpy_extras.io_utils import (
    ImportHelper,
    orientation_helper,
    axis_conversion)

from .stop_motion_obj import *

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


class SequenceImportSettings(bpy.types.PropertyGroup):
    fileNamePrefix: bpy.props.StringProperty(name='File Name')

    # material mode (one material total or one material per frame)
    perFrameMaterial: bpy.props.BoolProperty(
        name='Material per Frame',
        default=False)

    # Whether to load the entire sequence into memory or to load meshes on-demand
    cacheMode: bpy.props.EnumProperty(
        items=[('cached', 'Cached', 'The full sequence is loaded into memory and saved in the .blend file'),
               ('streaming', 'Streaming', 'The sequence is loaded on-demand and not saved in the .blend file')],
        name='Cache Mode',
        default='cached')
    fileFormat: bpy.props.EnumProperty(
        items=[('obj', 'OBJ', 'Wavefront OBJ'),
               ('stl', 'STL', 'STereoLithography'),
               ('ply', 'PLY', 'Stanford PLY')],
        name='File Format',
        default='obj')


@orientation_helper(axis_forward='-Z', axis_up='Y')
class ImportSequence(bpy.types.Operator, ImportHelper):
    """Load a mesh sequence"""
    bl_idname = "ms.import_sequence"
    bl_label = "Import"
    bl_options = {'UNDO'}

    objSettings: bpy.props.PointerProperty(type=OBJImporter)
    stlSettings: bpy.props.PointerProperty(type=STLImporter)
    plySettings: bpy.props.PointerProperty(type=PLYImporter)
    sequenceSettings: bpy.props.PointerProperty(type=SequenceImportSettings)

    def execute(self, context):
        print("Imported a sequence")
        if self.sequenceSettings.fileNamePrefix == "":
            self.report({'ERROR_INVALID_INPUT'}, "Please enter a file name prefix")
            return {'CANCELLED'}

        # the input parameters should be stored on 'self'
        # create a new mesh sequence
        seqObj = newMeshSequence()
        mss = seqObj.mesh_sequence_settings

        # deep copy self.sequenceSettings data into the new object's mss data, including dirPath
        mss.dirPath = self.filepath
        mss.fileName = self.sequenceSettings.fileNamePrefix
        mss.perFrameMaterial = self.sequenceSettings.perFrameMaterial
        mss.cacheMode = self.sequenceSettings.cacheMode
        mss.fileFormat = self.sequenceSettings.fileFormat

        if mss.fileFormat == 'obj':
            #setattr(seqObj.mesh_sequence_settings, "fileImporter", OBJImporter(self.objSettings))
            seqObj.mesh_sequence_settings.fileImporter = OBJImporter(self.objSettings)
            seqObj.mesh_sequence_settings.fileImporter.axis_forward = self.axis_forward
            seqObj.mesh_sequence_settings.fileImporter.axis_up = self.axis_up
        elif mss.fileFormat == 'stl':
            seqObj.mesh_sequence_settings.fileImporter = STLImporter(self.stlSettings)
            seqObj.mesh_sequence_settings.fileImporter.axis_forward = self.axis_forward
            seqObj.mesh_sequence_settings.fileImporter.axis_up = self.axis_up
        elif mss.fileFormat == 'ply':
            # currently, the PLY import addon doesn't support import transformations
            seqObj.mesh_sequence_settings.fileImporter = PLYImporter(self.plySettings)

        meshCount = 0

        # cached
        if mss.cacheMode == 'cached':
            meshCount = loadSequenceFromMeshFiles(seqObj, mss.dirPath, mss.fileName)

        # streaming
        elif mss.cacheMode == 'streaming':
            meshCount = loadStreamingSequenceFromMeshFiles(seqObj, mss.dirPath, mss.fileName)

        # reset self.sequenceSettings data to defaults
        self.sequenceSettings.fileNamePrefix = ""
        self.sequenceSettings.cacheMode = "cached"
        self.sequenceSettings.fileFormat = "obj"
        self.sequenceSettings.perFrameMaterial = False

        if meshCount == 0:
            self.report({'ERROR'}, "No matching files found. Make sure the Root Folder, File Name, and File Format are correct.")
            return {'CANCELLED'}

        return {'FINISHED'}

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
        layout.row().prop(op.sequenceSettings, "fileFormat")

        if op.sequenceSettings.fileFormat == 'obj':
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

        elif op.sequenceSettings.fileFormat == 'stl':
            layout.row().prop(op.stlSettings, "global_scale")
            layout.row().prop(op.stlSettings, "use_scene_unit")
            layout.row().prop(op.stlSettings, "use_facet_normal")
        elif op.sequenceSettings.fileFormat == 'ply':
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
        row = layout.row()
        if op.sequenceSettings.fileNamePrefix == "":
            row.alert = True

        row.prop(op.sequenceSettings, "fileNamePrefix")
        layout.row().prop(op.sequenceSettings, "perFrameMaterial")
        layout.row().prop(op.sequenceSettings, "cacheMode")


def menu_func_import_sequence(self, context):
    self.layout.operator(ImportSequence.bl_idname, text="Mesh Sequence")
