# ##### BEGIN GPL LICENSE BLOCK #####
#
#   Stop motion OBJ: A Mesh sequence importer for Blender
#   Copyright (C) 2016-2022  Justin Jensen
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
    bl_label = 'Stop Motion OBJ'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'

    @classmethod
    def poll(cls, context):
        return context.object.type == 'MESH'

    def draw(self, context):
        if context.object.type == 'MESH' and context.object.mesh_sequence_settings.initialized == False:
            # show button to convert the object into a mesh sequence
            self.layout.operator(ConvertToMeshSequence.bl_idname, icon="ONIONSKIN_ON")



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
            col.prop(objSettings, "frameMode")

            # keyframed playback
            if objSettings.frameMode == '4':
                row = col.row()
                if objSettings.curKeyframeMeshIdx <= 0 or objSettings.curKeyframeMeshIdx > objSettings.numMeshes - 1:
                    row.alert = True
                row.prop(objSettings, "curKeyframeMeshIdx")
            # all other playback modes
            else:
                col.prop(objSettings, "startFrame")
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


class SMO_PT_MeshSequenceExportPanel(bpy.types.Panel):
    bl_label = 'Export'
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
        inObjectMode = context.mode == 'OBJECT'
        inSculptMode = context.mode == 'SCULPT'

        if objSettings.isImported is True:
            # non-imported sequences won't have a fileName or dirPath and cannot be exported (for now)
            row = layout.row()
            row.enabled = inObjectMode or inSculptMode
            row.prop(objSettings, "autoExportChanges")
            
            row = layout.row()
            row.enabled = inObjectMode or inSculptMode
            row.prop(objSettings, "overwriteSrcDir")

            row = layout.row()
            row.enabled = (inObjectMode or inSculptMode) and objSettings.overwriteSrcDir is False
            row.alert = objSettings.exportDir == '' and objSettings.overwriteSrcDir is False

            row.prop(objSettings, "exportDir")

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
        inObjectMode = context.mode == 'OBJECT'
        inSculptMode = context.mode == 'SCULPT'
        if objSettings.loaded is True:
            # only allow mesh duplication for non-imported sequences in Keyframe playback mode
            if objSettings.isImported is False and objSettings.frameMode == '4':
                row = layout.row(align=True)
                row.enabled = inObjectMode or inSculptMode
                row.operator("ms.duplicate_mesh_frame")
            if objSettings.cacheMode == 'cached':
                row = layout.row(align=True)
                row.enabled = inObjectMode
                row.label(text="Shading:")
                row.operator("ms.batch_shade_smooth")
                row.operator("ms.batch_shade_flat")

                row = layout.row(align=True)
                row.enabled = inObjectMode
                row.operator("ms.merge_duplicate_materials")

                if objSettings.isImported is True:
                    # non-imported sequences won't have a fileName or dirPath and cannot be reloaded
                    row = layout.row()
                    row.enabled = inObjectMode
                    row.operator("ms.reload_mesh_sequence")

                row = layout.row()
                row.enabled = inObjectMode
                row.operator("ms.bake_sequence")
            
            

            row = layout.row()
            row.enabled = inObjectMode
            row.operator("ms.deep_delete_sequence")

            layout.row().separator()

            # we have to subtract one because numMeshes includes the empty mesh
            layout.row().label(text="Sequence size: " + str(objSettings.numMeshes - 1) + " meshes")

            if objSettings.cacheMode == 'streaming':
                layout.row().label(text="Cached meshes: " + str(objSettings.numMeshesInMemory)  + " meshes")

            if objSettings.isImported is True:
                # non-imported sequences won't have a dirPath to display
                layout.row().label(text="Mesh directory: " + objSettings.dirPath)
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
               ('ply', 'PLY', 'Stanford PLY'),
               ('x3d', 'X3D', 'X3D Extensible 3D')],
        name='File Format',
        default='obj')
    dirPathIsRelative: bpy.props.BoolProperty(
        name="Relative Paths",
        description="Store relative paths for Streaming sequences and for reloading Cached sequences",
        default=True)


@orientation_helper(axis_forward='-Z', axis_up='Y')
class ImportSequence(bpy.types.Operator, ImportHelper):
    """Load a mesh sequence"""
    bl_idname = "ms.import_sequence"
    bl_label = "Select Folder"
    bl_options = {'UNDO'}

    importSettings: bpy.props.PointerProperty(type=MeshImporter)
    sequenceSettings: bpy.props.PointerProperty(type=SequenceImportSettings)

    # for now, we'll just show any file type that Stop Motion OBJ supports
    filter_glob: bpy.props.StringProperty(default="*.stl;*.obj;*.mtl;*.ply;*.x3d")

    directory: bpy.props.StringProperty(subtype='DIR_PATH')

    axis_forward: bpy.props.StringProperty(default="-Z")
    axis_up: bpy.props.StringProperty(default="Y")

    def execute(self, context):
        if self.sequenceSettings.fileNamePrefix == "":
            self.report({'ERROR_INVALID_INPUT'}, "Please enter a file name prefix")
            return {'CANCELLED'}

        self.importSettings.axis_forward = self.axis_forward
        self.importSettings.axis_up = self.axis_up

        b_axis_forward = self.axis_forward
        b_axis_up = self.axis_up

        fileNames = self.sequenceSettings.fileNamePrefix.split(';')
        noMatchFileNames = []
        for fileNameRaw in filter(lambda f: f.strip() != '', fileNames):    # filter out any empty/whitespace strings
            # remove leading and trailing whitespace (might still contain folder name)
            fileName = fileNameRaw.strip()

            # construct the full absolute path
            absWildcardPath = os.path.join(self.directory, fileName + '*.' + self.sequenceSettings.fileFormat)

            # separate the directory from the file name
            basenamePrefix = os.path.basename(absWildcardPath).split('*')[0]

            # get the final directory path
            dirPath = os.path.dirname(absWildcardPath)

            # see whether these files exist before creating a sequence object
            if countMatchingFiles(dirPath, basenamePrefix, fileExtensionFromType(self.sequenceSettings.fileFormat)) > 0:
                # the input parameters should be stored on 'self'
                # create a new mesh sequence
                seqObj = newMeshSequence()
                global_matrix = axis_conversion(from_forward=b_axis_forward,from_up=b_axis_up).to_4x4()
                seqObj.matrix_world = global_matrix

                mss = seqObj.mesh_sequence_settings

                # deep copy self.sequenceSettings data into the new object's mss data, including dirPath
                mss.dirPath = dirPath
                mss.fileName = basenamePrefix
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

                self.resetToDefaults()

                if meshCount == 0:
                    # this section shouldn't be needed because we check above before creating the mesh sequence object
                    bpy.data.objects.remove(seqObj, do_unlink=True)
                    self.report({'ERROR'}, "No matching files found. Make sure the Root Folder, File Name, and File Format are correct.")
                    return {'CANCELLED'}
                
                # get the name of the first mesh, remove trailing numbers and _ and .
                firstMeshName = os.path.splitext(mss.meshNameArray[1].basename)[0].rstrip('._0123456789')
                seqObj.name = createUniqueName(firstMeshName + '_sequence', bpy.data.objects)
                seqObj.mesh_sequence_settings.isImported = True
            else:
                # this filename prefix had no matching files
                noMatchFileNames.append(fileName)
        
        if len(noMatchFileNames) > 0:
            self.report({'ERROR'}, "No matching files found for: " + " ".join(noMatchFileNames) + ". Make sure the File Name and Format are correct.")

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
        dest.obj_global_clamp_size = source.obj_global_clamp_size
        dest.stl_global_scale = source.stl_global_scale
        dest.stl_use_scene_unit = source.stl_use_scene_unit
        dest.stl_use_facet_normal = source.stl_use_facet_normal
    
    def resetToDefaults(self):
        self.sequenceSettings.fileNamePrefix = ""
        self.filepath = ""
        self.axis_forward = "-Z"
        self.axis_up = "Y"

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
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.row().prop(op.sequenceSettings, "fileFormat")

        if op.sequenceSettings.fileFormat == 'obj':
            layout.prop(op.importSettings, 'obj_use_image_search')
            layout.prop(op.importSettings, 'obj_use_smooth_groups')
            layout.prop(op.importSettings, 'obj_use_edges')
            layout.prop(op.importSettings, 'obj_global_clamp_size')

            col = layout.column()
            col.prop(op.importSettings, "obj_use_groups_as_vgroups")

        elif op.sequenceSettings.fileFormat == 'stl':
            layout.row().prop(op.importSettings, "stl_global_scale")
            layout.row().prop(op.importSettings, "stl_use_scene_unit")
            layout.row().prop(op.importSettings, "stl_use_facet_normal")
        elif op.sequenceSettings.fileFormat == 'ply':
            layout.label(text="No .ply settings")
        elif op.sequenceSettings.fileFormat == 'x3d':
            layout.label(text="No .x3d settings")


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


class ConvertToMeshSequence(bpy.types.Operator):
    """Convert to Mesh Sequence"""
    bl_idname = "ms.convert_to_mesh_sequence"
    bl_label = "Convert to Mesh Sequence"
    bl_options = {'UNDO'}

    def execute(self, context):
        obj = context.object

        # if this object is alread a mesh sequence object, return Failure
        if obj.mesh_sequence_settings.initialized is True:
            self.report({'ERROR'}, "The selected object is already a mesh sequence")
            return {'CANCELLED'}

        # hijack the mesh from the selected object and add it to a new mesh sequence
        msObj = newMeshSequence()
        msObj.mesh_sequence_settings.isImported = False
        addMeshToSequence(msObj, obj.data)

        # make sure the new mesh sequence has the same transform (especially the location) as context.object
        msObj.location = obj.location
        msObj.scale = obj.scale
        msObj.rotation_euler = obj.rotation_euler
        msObj.rotation_quaternion = obj.rotation_quaternion

        objName = obj.name
        msObj.name = objName + '_sequence'

        # delete the old object but not its mesh
        bpy.data.objects.remove(obj)

        # set the mesh sequence playback mode to Keyframe
        msObj.mesh_sequence_settings.frameMode = '4'

        # create a keyframe for this mesh at the current frame
        msObj.mesh_sequence_settings.curKeyframeMeshIdx = 1
        msObj.keyframe_insert(data_path='mesh_sequence_settings.curKeyframeMeshIdx', frame=context.scene.frame_current)
        
        # make the interpolation constant for the first keyframe
        meshIdxCurve = next((curve for curve in msObj.animation_data.action.fcurves if 'curKeyframeMeshIdx' in curve.data_path), None)
        keyAtFrame = next((keyframe for keyframe in meshIdxCurve.keyframe_points if keyframe.co.x == context.scene.frame_current), None)
        keyAtFrame.interpolation = 'CONSTANT'

        return {'FINISHED'}

def menu_func_convert_to_sequence(self, context):
    if context.object is not None:
        if context.object.type == 'MESH' and context.object.mesh_sequence_settings.initialized is False:
            self.layout.separator()
            self.layout.operator(ConvertToMeshSequence.bl_idname, icon="ONIONSKIN_ON")


class DuplicateMeshFrame(bpy.types.Operator):
    """Make a copy of the current mesh and create a keyframe for it at the current frame"""
    bl_idname = "ms.duplicate_mesh_frame"
    bl_label = "Duplicate Mesh Frame"
    bl_options = {'UNDO'}

    def execute(self, context):
        obj = context.object

        if obj is None:
            return {'CANCELLED'}

        # if this object is not a mesh sequence object, return Failure
        if obj.mesh_sequence_settings.initialized is False:
            self.report({'ERROR'}, "The selected object is not a mesh sequence")
            return {'CANCELLED'}

        # if the object doesn't have a 'curKeyframeMeshIdx' fcurve, we can't add a mesh to it
        meshIdxCurve = next((curve for curve in obj.animation_data.action.fcurves if 'curKeyframeMeshIdx' in curve.data_path), None)
        if meshIdxCurve is None:
            self.report({'ERROR'}, "The selected mesh sequence has no keyframe curve")
            return {'CANCELLED'}

        # if the keyframe curve already has a keyframe at this frame number, we can't create another one here
        keyAtFrame = next((keyframe for keyframe in meshIdxCurve.keyframe_points if keyframe.co.x == context.scene.frame_current), None)
        if keyAtFrame is not None:
            self.report({'ERROR'}, "There is already a keyframe at the current frame")
            return {'CANCELLED'}

        # make a copy of the current mesh
        newMesh = obj.data.copy()
        newMesh.use_fake_user = True
        newMesh.inMeshSequence = True

        # add the mesh to the end of the sequence
        meshIdx = addMeshToSequence(obj, newMesh)

        # add a new keyframe at this frame number for the new mesh
        obj.mesh_sequence_settings.curKeyframeMeshIdx = meshIdx
        obj.keyframe_insert(data_path='mesh_sequence_settings.curKeyframeMeshIdx', frame=context.scene.frame_current)
        
        # make the interpolation constant for this keyframe
        newKeyAtFrame = next((keyframe for keyframe in meshIdxCurve.keyframe_points if keyframe.co.x == context.scene.frame_current), None)
        newKeyAtFrame.interpolation = 'CONSTANT'

        return {'FINISHED'}

