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
import os
import re
import glob
from bpy.app.handlers import persistent


def alphanumKey(string):
    """ Turn a string into a list of string and number chunks.
        "z23a" -> ["z", 23, "a"]
    """
    return [int(c) if c.isdigit() else c for c in re.split('([0-9]+)', string)]


# global variable for the MeshSequenceController
MSC = None


def deselectAll():
    for ob in bpy.context.scene.objects:
        ob.select_set(state=False)

# set the frame number for all mesh sequence objects
# COMMENT THIS persistent OUT WHEN RUNNING FROM THE TEXT EDITOR
@persistent
def updateFrame(scene):
    scn = bpy.context.scene
    global MSC
    MSC.setFrame(scn.frame_current)


# runs every time the start frame of an object is changed
def updateStartFrame(self, context):
    updateFrame(0)
    return None


def countMatchingFiles(_directory, _filePrefix, _fileExtension):
    full_filepath = os.path.join(_directory, _filePrefix + '*.' + _fileExtension)
    print(full_filepath)
    files = glob.glob(full_filepath)
    print(files)
    return len(files)


def fileExtensionFromTypeNumber(_typeNumber):
    if(_typeNumber == 0):
        return 'obj'
    elif(_typeNumber == 1):
        return 'stl'
    elif(_typeNumber == 2):
        return 'ply'
    return ''


def importFuncFromTypeNumber(_typeNumber):
    if (_typeNumber == 0):
        return bpy.ops.import_scene.obj
    elif (_typeNumber == 1):
        return bpy.ops.import_mesh.stl
    elif (_typeNumber == 2):
        return bpy.ops.import_mesh.ply
    return None


class MeshSequenceSettings(bpy.types.PropertyGroup):
    dirPath: bpy.props.StringProperty(
        name="Root Folder",
        description="Only .OBJ files will be listed",
        subtype="DIR_PATH")
    fileName: bpy.props.StringProperty(name='File Name')
    startFrame: bpy.props.IntProperty(
        name='Start Frame',
        update=updateStartFrame,
        default=1)
    meshNames: bpy.props.StringProperty()
    numMeshes: bpy.props.IntProperty()
    initialized: bpy.props.BoolProperty(default=False)
    loaded: bpy.props.BoolProperty(default=False)

    # out-of-range frame mode
    frameMode: bpy.props.EnumProperty(
        items=[('0', 'Blank', 'Object disappears when frame is out of range'),
               ('1', 'Extend', 'First and last frames are duplicated'),
               ('2', 'Repeat', 'Repeat the animation'),
               ('3', 'Bounce', 'Play in reverse at the end of the frame range')],
        name='Frame Mode',
        default='1')

    # material mode (one material total or one material per frame)
    perFrameMaterial: bpy.props.BoolProperty(
        name='Material per Frame',
        default=False
    )

    speed: bpy.props.FloatProperty(
        name='Playback Speed',
        min=0.0001,
        soft_min=0.01,
        step=25,
        precision=2,
        default=1
    )

    fileFormat: bpy.props.EnumProperty(
        items=[('0', 'OBJ', 'Wavefront OBJ'),
               ('1', 'STL', 'STereoLithography'),
               ('2', 'PLY', 'Stanford PLY')],
        name='File Format',
        default='0')


class MeshSequenceController:
    def __init__(self):
        for obj in bpy.data.objects:
            if obj.mesh_sequence_settings.initialized is True:
                self.loadSequenceFromData(obj)
        self.freeUnusedMeshes()

    def newMeshSequence(self):
        bpy.ops.object.add(type='MESH')
        # this new object should be the currently-selected object
        theObj = bpy.context.object
        theObj.name = 'sequence'
        theMesh = theObj.data
        theMesh.name = 'emptyMesh'
        theMesh.use_fake_user = True
        theMesh.inMeshSequence = True
        # add the mesh's name to the object's mesh_sequence_settings
        theObj.mesh_sequence_settings.meshNames = theMesh.name + '/'

        deselectAll()
        theObj.select_set(state=True)

        theObj.mesh_sequence_settings.initialized = True
        return theObj

    def loadSequenceFromFile(self, _obj, _dir, _file):
        deselectAll()

        # error out early if there are no files that match the file prefix
        fileExtension = fileExtensionFromTypeNumber(int(_obj.mesh_sequence_settings.fileFormat))
        if countMatchingFiles(_dir, _file, fileExtension) == 0:
            return 0

        scn = bpy.context.scene
        importFunc = importFuncFromTypeNumber(int(_obj.mesh_sequence_settings.fileFormat))

        full_dirpath = bpy.path.abspath(_dir)
        full_filepath = os.path.join(full_dirpath, _file + '*.' + fileExtension)

        numFrames = 0
        unsortedFiles = glob.glob(full_filepath)
        sortedFiles = sorted(unsortedFiles, key=alphanumKey)

        for file in sortedFiles:
            # import the mesh file
            importFunc(filepath=file)
            tmpObject = bpy.context.selected_objects[0]
            # IMPORTANT: don't copy it; just copy the pointer. This cuts memory usage in half.
            tmpMesh = tmpObject.data
            tmpMesh.use_fake_user = True
            tmpMesh.inMeshSequence = True
            deselectAll()
            tmpObject.select_set(state=True)
            bpy.ops.object.delete()
            # add the new mesh's name to the sequence object's text property
            # add the '/' character as a delimiter
            # http://stackoverflow.com/questions/1976007/what-characters-are-forbidden-in-windows-and-linux-directory-names
            _obj.mesh_sequence_settings.meshNames += tmpMesh.name + '/'
            numFrames += 1

        _obj.mesh_sequence_settings.numMeshes = numFrames + 1
        if(numFrames > 0):
            # remove the last '/' from the string
            _obj.mesh_sequence_settings.meshNames = _obj.mesh_sequence_settings.meshNames[:-1]
            self.setFrameObj(_obj, scn.frame_current)

            _obj.select_set(state=True)
            _obj.mesh_sequence_settings.loaded = True

        return numFrames

    # this is used when a mesh sequence object has been saved and subsequently found in a .blend file
    def loadSequenceFromData(self, _obj):
        scn = bpy.context.scene
        t_meshNames = _obj.mesh_sequence_settings.meshNames.split('/')
        # count the number of mesh names (helps with backwards compatibility)
        _obj.mesh_sequence_settings.numMeshes = len(t_meshNames)

        # make sure the meshes know they're part of a mesh sequence (helps with backwards compatibility)
        for t_meshName in t_meshNames:
            bpy.data.meshes[t_meshName].inMeshSequence = True

        deselectAll()

        scn.objects.active = _obj
        _obj.select = True
        self.setFrameObj(_obj, scn.frame_current)

        _obj.mesh_sequence_settings.loaded = True

    def reloadSequenceFromFile(self, _object, _directory, _filePrefix):
        # if there are no files that match the file prefix, error out early before making changes
        fileExtension = fileExtensionFromTypeNumber(int(_object.mesh_sequence_settings.fileFormat))
        if countMatchingFiles(_directory, _filePrefix, fileExtension) == 0:
            return 0

        # mark the existing meshes for cleanup (keep the first 'emptyMesh' one)
        for meshName in _object.mesh_sequence_settings.meshNames.split('/')[1:]:
            bpy.data.meshes[meshName].use_fake_user = False
            bpy.data.meshes[meshName].inMeshSequence = False

        # re-initialize _object.meshNames
        _object.mesh_sequence_settings.meshNames = 'emptyMesh/'

        # temporarily set the speed to 1 while we reload
        originalSpeed = _object.mesh_sequence_settings.speed
        _object.mesh_sequence_settings.speed = 1.0

        numMeshes = self.loadSequenceFromFile(_object, _directory, _filePrefix)

        # set the speed back to its previous value
        _object.mesh_sequence_settings.speed = originalSpeed

        return numMeshes

    def getMesh(self, _obj, _idx):
        names = _obj.mesh_sequence_settings.meshNames.split('/')
        name = names[_idx]
        return bpy.data.meshes[name]

    def setFrame(self, _frame):
        for obj in bpy.data.objects:
            if obj.mesh_sequence_settings.initialized is True and obj.mesh_sequence_settings.loaded is True:
                self.setFrameObj(obj, _frame)

    def getMeshIdxFromFrame(self, _obj, _frameNum):
        numFrames = _obj.mesh_sequence_settings.numMeshes - 1
        # convert the frame number into an array index
        idx = _frameNum - (_obj.mesh_sequence_settings.startFrame - 1)
        # adjust for playback speed
        idx = int(idx * _obj.mesh_sequence_settings.speed)
        frameMode = int(_obj.mesh_sequence_settings.frameMode)
        # 0: Blank
        if(frameMode == 0):
            if(idx < 1 or idx >= numFrames + 1):
                idx = 0
        # 1: Extend (default)
        elif(frameMode == 1):
            if(idx < 1):
                idx = 1
            elif(idx >= numFrames + 1):
                idx = numFrames
        # 2: Repeat
        elif(frameMode == 2):
            idx = ((idx - 1) % (numFrames)) + 1
        # 3: Bounce
        elif(frameMode == 3):
            idx -= 1
            tmp = int(idx / numFrames)
            if(tmp % 2 == 0):
                idx = idx % numFrames
            else:
                idx = (numFrames - 1) - (idx % numFrames)
            idx += 1
        return idx

    def setFrameObj(self, _obj, _frameNum):
        # store the current mesh for grabbing the material later
        prev_mesh = _obj.data
        idx = self.getMeshIdxFromFrame(_obj, _frameNum)
        next_mesh = self.getMesh(_obj, idx)

        if (next_mesh != prev_mesh):
            # swap the meshes
            _obj.data = next_mesh

            if _obj.mesh_sequence_settings.perFrameMaterial is False:
                # if the previous mesh had a material, copy it to the new one
                if(len(prev_mesh.materials) > 0):
                    _obj.data.materials.clear()
                    for material in prev_mesh.materials:
                        _obj.data.materials.append(material)

    def shadeSequence(self, _obj, _smooth):
        deselectAll()
        _obj.select_set(state=True)
        # grab the current mesh so we can put it back later
        origMesh = _obj.data
        for idx in range(1, _obj.mesh_sequence_settings.numMeshes):
            _obj.data = self.getMesh(_obj, idx)
            if(_smooth):
                bpy.ops.object.shade_smooth()
            else:
                bpy.ops.object.shade_flat()
        # reset the sequence's mesh to the right one based on the current frame
        _obj.data = origMesh

    def bakeSequence(self, _obj):
        scn = bpy.context.scene
        activeCollection = bpy.context.collection
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        containerObj = bpy.context.active_object
        # rename the container object to "C_{object's current name}" ('C' stands for 'Container')
        newName = "C_" + _obj.name
        containerObj.name = newName

        # copy the object's transformation data into the container
        containerObj.location = _obj.location
        containerObj.scale = _obj.scale
        containerObj.rotation_euler = _obj.rotation_euler
        containerObj.rotation_quaternion = _obj.rotation_quaternion

        # copy the object's animation data into the container
        # http://blender.stackexchange.com/questions/27136/how-to-copy-keyframes-from-one-action-to-other
        if _obj.animation_data is not None:
            seq_anim = _obj.animation_data
            properties = [p.identifier for p in seq_anim.bl_rna.properties if not p.is_readonly]
            if containerObj.animation_data is None:
                containerObj.animation_data_create()
            container_anim = containerObj.animation_data
            for prop in properties:
                setattr(container_anim, prop, getattr(seq_anim, prop))

        # create a dictionary mapping meshes to new objects, meshToObject
        meshToObject = {}

        meshNames = _obj.mesh_sequence_settings.meshNames.split('/')
        # for each mesh (including the empty mesh):
        for meshName in meshNames:
            currentMesh = bpy.data.meshes[meshName]
            # even though it's kinda still part of a mesh sequence, it's not really anymore
            currentMesh.inMeshSequence = False
            tmpObj = bpy.data.objects.new('o_' + currentMesh.name, currentMesh)
            activeCollection.objects.link(tmpObj)
            currentMesh.use_fake_user = False
            meshToObject[currentMesh] = tmpObj
            # in the object, add keyframes at frames 0 and the last frame of the animation:
            tmpObj.hide_viewport = True
            tmpObj.keyframe_insert(data_path='hide_viewport', frame=scn.frame_start)
            tmpObj.keyframe_insert(data_path='hide_viewport', frame=scn.frame_end)

            tmpObj.hide_render = True
            tmpObj.keyframe_insert(data_path='hide_render', frame=scn.frame_start)
            tmpObj.keyframe_insert(data_path='hide_render', frame=scn.frame_end)

            tmpObj.parent = containerObj

        # If this is a single-material sequence, make sure the material is copied to the whole sequence
        # This assumes that the first mesh in the sequence has a material
        if _obj.mesh_sequence_settings.perFrameMaterial is False:
            objMaterials = bpy.data.meshes[meshNames[1]].materials
            meshesIter = iter(meshNames)
            # skip the emptyMesh
            next(meshesIter)
            # skip the first mesh (we'll copy the material from this one into the rest of them)
            next(meshesIter)
            for meshName in meshesIter:
                currentMesh = bpy.data.meshes[meshName]
                currentMesh.materials.clear()
                for material in objMaterials:
                    currentMesh.materials.append(material)

        for frameNum in range(scn.frame_start, scn.frame_end + 1):
            # figure out which mesh is visible
            idx = self.getMeshIdxFromFrame(_obj, frameNum)
            frameMesh = self.getMesh(_obj, idx)

            # use the dictionary to find which object the mesh belongs to
            frameObj = meshToObject[frameMesh]

            # add two keyframes to the object at the current frame:
            frameObj.hide_viewport = False
            frameObj.keyframe_insert(data_path='hide_viewport', frame=frameNum)

            frameObj.hide_render = False
            frameObj.keyframe_insert(data_path='hide_render', frame=frameNum)

            # add two keyframes to the object at the next frame:
            frameObj.hide_viewport = True
            frameObj.keyframe_insert(data_path='hide_viewport', frame=frameNum + 1)

            frameObj.hide_render = True
            frameObj.keyframe_insert(data_path='hide_render', frame=frameNum + 1)

        # delete the sequence object
        deselectAll()
        _obj.select_set(state=True)
        bpy.ops.object.delete()

    def freeUnusedMeshes(self):
        numFreed = 0
        for t_mesh in bpy.data.meshes:
            if t_mesh.inMeshSequence is True:
                t_mesh.use_fake_user = False
                numFreed += 1
        for t_obj in bpy.data.objects:
            if t_obj.mesh_sequence_settings.initialized is True and t_obj.mesh_sequence_settings.loaded is True:
                t_meshNames = t_obj.mesh_sequence_settings.meshNames
                for t_meshName in t_meshNames.split('/'):
                    bpy.data.meshes[t_meshName].use_fake_user = True
                    numFreed -= 1
        # the remaining meshes with no real or fake users will be garbage collected when Blender is closed
        print(numFreed, " meshes freed")

# COMMENT THIS persistent OUT WHEN RUNNING FROM THE TEXT EDITOR
@persistent
def initSequenceController(scene):
    global MSC
    MSC = MeshSequenceController()


class AddMeshSequence(bpy.types.Operator):
    """Add Mesh Sequence"""
    # what the operator is called
    bl_idname = "ms.add_mesh_sequence"
    # what shows up in the menu
    bl_label = "Mesh Sequence"
    bl_options = {'UNDO'}

    def execute(self, context):
        global MSC
        MSC.newMeshSequence()
        return {'FINISHED'}


# the function for adding "Mesh Sequence" to the Add > Mesh menu
def menu_func(self, context):
    self.layout.operator(AddMeshSequence.bl_idname, icon="PLUGIN")


class LoadMeshSequence(bpy.types.Operator):
    """Load Mesh Sequence"""
    bl_idname = "ms.load_mesh_sequence"
    bl_label = "Load Mesh Sequence"
    bl_options = {'UNDO'}

    def execute(self, context):
        global MSC
        obj = context.object
        dirPath = obj.mesh_sequence_settings.dirPath
        fileName = obj.mesh_sequence_settings.fileName

        num = MSC.loadSequenceFromFile(obj, dirPath, fileName)
        if(num == 0):
            self.report({'ERROR'}, "No matching files found. Make sure the Root Folder, File Name, and File Format are correct.")
            return {'CANCELLED'}

        return {'FINISHED'}


class ReloadMeshSequence(bpy.types.Operator):
    """Reload From Disk"""
    bl_idname = "ms.reload_mesh_sequence"
    bl_label = "Reload From Disk"
    bl_options = {'UNDO'}

    def execute(self, context):
        global MSC
        obj = context.object
        dirPath = obj.mesh_sequence_settings.dirPath
        fileName = obj.mesh_sequence_settings.fileName

        num = MSC.reloadSequenceFromFile(obj, dirPath, fileName)
        if (num == 0):
            self.report({'ERROR'}, "Invalid file path. Make sure the Root Folder, File Name, and File Format are correct.")
            return {'CANCELLED'}

        return {'FINISHED'}


class BatchShadeSmooth(bpy.types.Operator):
    """Smooth Shade Sequence"""
    bl_idname = "ms.batch_shade_smooth"
    bl_label = "Smooth"
    bl_options = {'UNDO'}

    def execute(self, context):
        global MSC
        obj = context.object
        # True for smooth
        MSC.shadeSequence(obj, True)
        return {'FINISHED'}


class BatchShadeFlat(bpy.types.Operator):
    """Flat Shade Sequence"""
    bl_idname = "ms.batch_shade_flat"
    bl_label = "Flat"
    bl_options = {'UNDO'}

    def execute(self, context):
        global MSC
        obj = context.object
        # False for flat
        MSC.shadeSequence(obj, False)
        return {'FINISHED'}


class BakeMeshSequence(bpy.types.Operator):
    """Bake Mesh Sequence"""
    bl_idname = "ms.bake_sequence"
    bl_label = "Bake Mesh Sequence"
    bl_options = {'UNDO'}

    def execute(self, context):
        global MSC
        obj = context.object
        MSC.bakeSequence(obj)
        # update the frame so the right shape is visible
        bpy.context.scene.frame_current = bpy.context.scene.frame_current
        return {'FINISHED'}


# The properties panel added to the Object Properties Panel list
class MeshSequencePanel(bpy.types.Panel):
    bl_idname = 'OBJ_SEQUENCE_PT_properties'
    bl_label = 'Mesh Sequence'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'

    def draw(self, context):
        layout = self.layout
        obj = context.object

        objSettings = obj.mesh_sequence_settings
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
                row.operator("ms.load_mesh_sequence")

            if objSettings.loaded is True:
                row = layout.row()
                row.prop(objSettings, "startFrame")

                row = layout.row()
                row.prop(objSettings, "frameMode")

                row = layout.row()
                row.prop(objSettings, "speed")

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
