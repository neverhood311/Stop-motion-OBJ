# ##### BEGIN GPL LICENSE BLOCK #####
#
#   Stop motion OBJ: A Mesh sequence importer for Blender
#   Copyright (C) 2016-2020  Justin Jensen
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy_extras.io_utils import (
    ImportHelper,
    orientation_helper,
    axis_conversion)

from .stop_motion_obj import *

# The properties panel added to the Object Properties Panel list
class SMO_PT_MeshSequencePanel(bpy.types.Panel):
    bl_idname = 'OBJ_SEQUENCE_PT_properties'
    bl_label = 'Mesh Sequence'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'

    @classmethod
    def poll(cls, context):
        return context.object.mesh_sequence_settings.initialized == True

    def draw(self, context):
        pass


class SMO_PT_MeshSequencePlaybackPanel(bpy.types.Panel):
    bl_label = 'Playback'
    bl_parent_id = "OBJ_SEQUENCE_PT_properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    @classmethod
    def poll(cls, context):
        return context.object.mesh_sequence_settings.initialized == True
    
    def draw(self, context):
        layout = self.layout
        objSettings = context.object.mesh_sequence_settings
        if objSettings.initialized is True and objSettings.loaded is True:
            layout.use_property_split = True
            layout.use_property_decorate = False
            col = layout.column(align=False)
            col.prop(objSettings, "startFrame")
            col.prop(objSettings, "frameMode")
            col.prop(objSettings, "speed")


class SMO_PT_MeshSequenceStreamingPanel(bpy.types.Panel):
    bl_label = 'Streaming'
    bl_parent_id = "OBJ_SEQUENCE_PT_properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'

    @classmethod
    def poll(cls, context):
        mss = context.object.mesh_sequence_settings
        return mss.initialized == True and mss.cacheMode == 'streaming'
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        objSettings = context.object.mesh_sequence_settings
        col = layout.column(align=False)
        col.prop(objSettings, "cacheSize")
        col.prop(objSettings, "streamDuringPlayback")


class SMO_PT_MeshSequenceAdvancedPanel(bpy.types.Panel):
    bl_label = 'Advanced'
    bl_parent_id = "OBJ_SEQUENCE_PT_properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.object.mesh_sequence_settings.initialized == True

    def draw(self, context):
        layout = self.layout
        objSettings = context.object.mesh_sequence_settings
        if objSettings.loaded is True:
            if objSettings.cacheMode == 'cached':
                row = layout.row(align=True)
                row.enabled = context.mode == 'OBJECT'
                row.label(text="Shading:")
                row.operator("ms.batch_shade_smooth")
                row.operator("ms.batch_shade_flat")

                row = layout.row()
                row.enabled = context.mode == 'OBJECT'
                row.operator("ms.reload_mesh_sequence")

                row = layout.row()
                row.enabled = context.mode == 'OBJECT'
                row.operator("ms.bake_sequence")

            row = layout.row()
            row.enabled = context.mode == 'OBJECT'
            row.operator("ms.deep_delete_sequence")

            layout.row().separator()
            layout.row().label(text="Sequence version: " + objSettings.version.toString())


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
    dirPathIsRelative: bpy.props.BoolProperty(
        name="Relative Paths",
        description="Store relative paths for Streaming sequences and for reloading Cached sequences",
        default=False)


@orientation_helper(axis_forward='-Z', axis_up='Y')
class ImportSequence(bpy.types.Operator, ImportHelper):
    """Load a mesh sequence"""
    bl_idname = "ms.import_sequence"
    bl_label = "Select Folder"
    bl_options = {'UNDO'}

    importSettings: bpy.props.PointerProperty(type=MeshImporter)
    sequenceSettings: bpy.props.PointerProperty(type=SequenceImportSettings)

    # for now, we'll just show any file type that Stop Motion OBJ supports
    filter_glob: bpy.props.StringProperty(default="*.stl;*.obj;*.mtl;*.ply")

    def execute(self, context):
        if self.sequenceSettings.fileNamePrefix == "":
            self.report({'ERROR_INVALID_INPUT'}, "Please enter a file name prefix")
            return {'CANCELLED'}

        # TODO: do we actually need to store these? It's encoded in the rotation of seqObj
        self.importSettings.axis_forward = self.axis_forward
        self.importSettings.axis_up = self.axis_up

        # the input parameters should be stored on 'self'
        # create a new mesh sequence
        seqObj = newMeshSequence()
        global_matrix = axis_conversion(from_forward=self.axis_forward,from_up=self.axis_up).to_4x4()
        seqObj.matrix_world = global_matrix

        mss = seqObj.mesh_sequence_settings

        # deep copy self.sequenceSettings data into the new object's mss data, including dirPath
        mss.dirPath = self.filepath
        mss.fileName = self.sequenceSettings.fileNamePrefix
        mss.perFrameMaterial = self.sequenceSettings.perFrameMaterial
        mss.cacheMode = self.sequenceSettings.cacheMode
        mss.fileFormat = self.sequenceSettings.fileFormat
        mss.dirPathIsRelative = self.sequenceSettings.dirPathIsRelative

        # this needs to be set to True if dirPath is supposed to be relative
        # once the path is made relative, it will be set to False
        mss.dirPathNeedsRelativizing = mss.dirPathIsRelative
        
        self.copyImportSettings(self.importSettings, mss.fileImporter)

        meshCount = 0

        # cached
        if mss.cacheMode == 'cached':
            meshCount = loadSequenceFromMeshFiles(seqObj, mss.dirPath, mss.fileName)

        # streaming
        elif mss.cacheMode == 'streaming':
            meshCount = loadStreamingSequenceFromMeshFiles(seqObj, mss.dirPath, mss.fileName)

        # reset self.sequenceSettings data to defaults
        # TODO: let's put this in a function
        self.sequenceSettings.fileNamePrefix = ""
        self.sequenceSettings.cacheMode = "cached"
        self.sequenceSettings.fileFormat = "obj"
        self.sequenceSettings.perFrameMaterial = False

        # TODO: do we need these? I thought they were already set above using axis_conversion
        self.axis_forward = "-Z"
        self.axis_up = "Y"

        if meshCount == 0:
            self.report({'ERROR'}, "No matching files found. Make sure the Root Folder, File Name, and File Format are correct.")
            return {'CANCELLED'}
        
        # get the name of the first mesh, remove trailing numbers and _ and .
        firstMeshName = os.path.splitext(mss.meshNameArray[1].basename)[0].rstrip('._0123456789')
        seqObj.name = firstMeshName + '_sequence'

        return {'FINISHED'}

    def copyImportSettings(self, source, dest):
        dest.axis_forward = source.axis_forward
        dest.axis_up = source.axis_up
        dest.obj_use_edges = source.obj_use_edges
        dest.obj_use_smooth_groups = source.obj_use_smooth_groups
        dest.obj_use_split_objects = False
        dest.obj_use_split_groups = False
        dest.obj_use_groups_as_vgroups = source.obj_use_groups_as_vgroups
        dest.obj_use_image_search = source.obj_use_image_search
        dest.obj_split_mode = "OFF"
        dest.obj_global_clight_size = source.obj_global_clight_size
        dest.stl_global_scale = source.stl_global_scale
        dest.stl_use_scene_unit = source.stl_use_scene_unit
        dest.stl_use_facet_normal = source.stl_use_facet_normal

    # we need this function so it doesn't try to render any UI elements. The ImportSequencePanel will do all the drawing
    def draw(self, context):
        pass


class SMO_PT_FileImportSettingsPanel(bpy.types.Panel):
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
            layout.prop(op.importSettings, 'obj_use_image_search')
            layout.prop(op.importSettings, 'obj_use_smooth_groups')
            layout.prop(op.importSettings, 'obj_use_edges')
            layout.prop(op.importSettings, 'obj_global_clight_size')

            col = layout.column()
            col.prop(op.importSettings, "obj_use_groups_as_vgroups")

        elif op.sequenceSettings.fileFormat == 'stl':
            layout.row().prop(op.importSettings, "stl_global_scale")
            layout.row().prop(op.importSettings, "stl_use_scene_unit")
            layout.row().prop(op.importSettings, "stl_use_facet_normal")
        elif op.sequenceSettings.fileFormat == 'ply':
            layout.label(text="No .ply settings")


class SMO_PT_TransformSettingsPanel(bpy.types.Panel):
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


class SMO_PT_SequenceImportSettingsPanel(bpy.types.Panel):
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
        layout.use_property_split = True
        layout.use_property_decorate = False
        col = layout.column(align=False)

        row = col.row()
        if op.sequenceSettings.fileNamePrefix == "":
            row.alert = True
        row.prop(op.sequenceSettings, "fileNamePrefix")
        col.prop(op.sequenceSettings, "cacheMode")
        col.prop(op.sequenceSettings, "perFrameMaterial")
        col.prop(op.sequenceSettings, "dirPathIsRelative")


def menu_func_import_sequence(self, context):
    self.layout.operator(ImportSequence.bl_idname, text="Mesh Sequence")
