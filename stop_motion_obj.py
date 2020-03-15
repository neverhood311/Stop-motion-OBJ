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


def deselectAll():
    for ob in bpy.context.scene.objects:
        ob.select_set(state=False)


# We have to use this function instead of bpy.context.selected_objects because there's no "selected_objects" within the render context
def getSelectedObjects():
    selected_objects = []
    for ob in bpy.context.scene.objects:
        if ob.select_get() is True:
            selected_objects.append(ob)
    return selected_objects

# set the frame number for all mesh sequence objects
# COMMENT THIS persistent OUT WHEN RUNNING FROM THE TEXT EDITOR
@persistent
def updateFrame(scene):
    scn = bpy.context.scene
    setFrameNumber(scn.frame_current)


# runs every time the start frame of an object is changed
def updateStartFrame(self, context):
    updateFrame(0)
    return None


def countMatchingFiles(_directory, _filePrefix, _fileExtension):
    full_filepath = os.path.join(_directory, _filePrefix + '*.' + _fileExtension)
    files = glob.glob(full_filepath)
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


class MeshNameProp(bpy.types.PropertyGroup):
    key: bpy.props.StringProperty()
    basename: bpy.props.StringProperty()
    inMemory: bpy.props.BoolProperty(default=False)


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
    # TODO: deprecate meshNames
    meshNames: bpy.props.StringProperty()
    meshNameArray: bpy.props.CollectionProperty(type=MeshNameProp)
    numMeshes: bpy.props.IntProperty()
    numMeshesInMemory: bpy.props.IntProperty(default=0)
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
        default=False)

    # Whether to load the entire sequence into memory or to load meshes on-demand
    cacheMode: bpy.props.EnumProperty(
        items=[('0', 'Cached', 'The full sequence is loaded into memory and saved in the .blend file'),
               ('1', 'Streaming', 'The sequence is loaded on-demand and not saved in the .blend file')],
        name='Cache Mode',
        default='0')

    # the number of frames to keep in memory if you're in streaming mode
    cacheSize: bpy.props.IntProperty(
        name='Cache Size',
        min=0,
        description='The maximum number of meshes to keep in memory. If >1, meshes will be removed from memory as new ones are loaded. If 0, all meshes will be kept.')

    # whether to enable/disable loading frames as they're required
    streamDuringPlayback: bpy.props.BoolProperty(
        name='Stream Meshes During Playback',
        description='Load meshes into memory as they are needed. If not checked, only the meshes currently in memory will appear.',
        default=True)

    speed: bpy.props.FloatProperty(
        name='Playback Speed',
        min=0.0001,
        soft_min=0.01,
        step=25,
        precision=2,
        default=1)

    fileFormat: bpy.props.EnumProperty(
        items=[('0', 'OBJ', 'Wavefront OBJ'),
               ('1', 'STL', 'STereoLithography'),
               ('2', 'PLY', 'Stanford PLY')],
        name='File Format',
        default='0')


@persistent
def initializeSequences(scene):
    for obj in bpy.data.objects:
        if obj.mesh_sequence_settings.initialized is True:
            loadCachedSequenceFromBlendFile(obj)
    freeUnusedMeshes()


def newMeshSequence():
    bpy.ops.object.add(type='MESH')
    # this new object should be the currently-selected object
    theObj = bpy.context.object
    theObj.name = 'sequence'
    theMesh = theObj.data
    theMesh.name = 'emptyMesh'
    theMesh.use_fake_user = True
    theMesh.inMeshSequence = True
    # add the mesh's name to the object's mesh_sequence_settings
    emptyMeshNameElement = theObj.mesh_sequence_settings.meshNameArray.add()
    emptyMeshNameElement.key = theMesh.name
    emptyMeshNameElement.inMemory = True

    deselectAll()
    theObj.select_set(state=True)

    theObj.mesh_sequence_settings.initialized = True
    return theObj


def loadStreamedSequenceFromMeshFiles(obj, directory, filePrefix):
    # count the number of matching files
    absDirectory = bpy.path.abspath(directory)
    fileExtension = fileExtensionFromTypeNumber(int(obj.mesh_sequence_settings.fileFormat))
    if countMatchingFiles(absDirectory, filePrefix, fileExtension) == 0:
        return 0

    # load the first frame
    importFunc = importFuncFromTypeNumber(int(obj.mesh_sequence_settings.fileFormat))
    wildcardAbsPath = os.path.join(absDirectory, filePrefix + '*.' + fileExtension)
    numFrames = 0
    numFramesInMemory = 0
    unsortedFilenames = glob.glob(wildcardAbsPath)
    sortedFilenames = sorted(unsortedFilenames, key=alphanumKey)
    deselectAll()
    for filename in sortedFilenames:
        newMeshNameElement = obj.mesh_sequence_settings.meshNameArray.add()
        newMeshNameElement.basename = os.path.basename(filename)
        newMeshNameElement.inMemory = False

        # if this is the first one, import it
        '''if numFrames == 0:
            importFunc(filepath=filename)
            tmpObject = bpy.context.selected_objects[0]
            tmpMesh = tmpObject.data
            tmpMesh.use_fake_user = True
            tmpMesh.inMeshSequence = True
            deselectAll()
            tmpObject.select_set(state=True)
            bpy.ops.object.delete()
            newMeshNameElement.key = tmpMesh.name
            newMeshNameElement.inMemory = True
            numFramesInMemory += 1'''

        numFrames += 1

    obj.mesh_sequence_settings.numMeshes = numFrames + 1
    obj.mesh_sequence_settings.numMeshesInMemory = numFramesInMemory

    if numFrames > 0:
        obj.mesh_sequence_settings.loaded = True

        setFrameObjStreamed(obj, bpy.context.scene.frame_current)

        # TODO: this select_set is not working
        obj.select_set(state=True)
    return numFrames


def loadSequenceFromMeshFiles(_obj, _dir, _file):
    # error out early if there are no files that match the file prefix
    full_dirpath = bpy.path.abspath(_dir)
    fileExtension = fileExtensionFromTypeNumber(int(_obj.mesh_sequence_settings.fileFormat))
    if countMatchingFiles(full_dirpath, _file, fileExtension) == 0:
        return 0

    importFunc = importFuncFromTypeNumber(int(_obj.mesh_sequence_settings.fileFormat))
    full_filepath = os.path.join(full_dirpath, _file + '*.' + fileExtension)
    numFrames = 0
    unsortedFiles = glob.glob(full_filepath)
    sortedFiles = sorted(unsortedFiles, key=alphanumKey)

    deselectAll()
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

        newMeshNameElement = _obj.mesh_sequence_settings.meshNameArray.add()
        newMeshNameElement.key = tmpMesh.name
        newMeshNameElement.basename = os.path.basename(file)
        newMeshNameElement.inMemory = True
        numFrames += 1

    _obj.mesh_sequence_settings.numMeshes = numFrames + 1
    _obj.mesh_sequence_settings.numMeshesInMemory = numFrames
    if(numFrames > 0):
        setFrameObj(_obj, bpy.context.scene.frame_current)

        _obj.select_set(state=True)
        _obj.mesh_sequence_settings.loaded = True

    return numFrames


# this is used when a mesh sequence object has been saved and subsequently found in a .blend file
def loadCachedSequenceFromBlendFile(_obj):
    scn = bpy.context.scene
    # if meshNames is not blank, we have an old file that must be converted to the new CollectionProperty format
    if _obj.mesh_sequence_settings.meshNames:
        # split meshNames
        # store them in mesh_sequence_settings.meshNameArray
        for meshName in _obj.mesh_sequence_settings.meshNames.split('/'):
            meshNameArrayElement = _obj.mesh_sequence_settings.meshNameArray.add()
            meshNameArrayElement.key = meshName
            meshNameArrayElement.inMemory = True

    # count the number of mesh names (helps with backwards compatibility)
    _obj.mesh_sequence_settings.numMeshes = len(_obj.mesh_sequence_settings.meshNameArray)
    _obj.mesh_sequence_settings.numMeshesInMemory = len(_obj.mesh_sequence_settings.meshNameArray) - 1

    # make sure the meshes know they're part of a mesh sequence (helps with backwards compatibility)
    for meshName in _obj.mesh_sequence_settings.meshNameArray:
        bpy.data.meshes[meshName.name].inMeshSequence = True

    deselectAll()

    _obj.select_set(state=True)
    setFrameObj(_obj, scn.frame_current)

    _obj.mesh_sequence_settings.loaded = True


def reloadSequenceFromMeshFiles(_object, _directory, _filePrefix):
    # if there are no files that match the file prefix, error out early before making changes
    fileExtension = fileExtensionFromTypeNumber(int(_object.mesh_sequence_settings.fileFormat))
    if countMatchingFiles(_directory, _filePrefix, fileExtension) == 0:
        return 0

    meshNamesArray = _object.mesh_sequence_settings.meshNameArray
    # mark the existing meshes for cleanup (keep the first 'emptyMesh' one)
    for meshNameElement in meshNamesArray[1:]:
        bpy.data.meshes[meshNameElement.key].use_fake_user = False
        bpy.data.meshes[meshNameElement.key].inMeshSequence = False

    # re-initialize _object.meshNameArray
    emptyMeshName = meshNamesArray[0].key
    meshNamesArray.clear()
    emptyMeshNameElement = meshNamesArray.add()
    emptyMeshNameElement.key = emptyMeshName

    # temporarily set the speed to 1 while we reload
    originalSpeed = _object.mesh_sequence_settings.speed
    _object.mesh_sequence_settings.speed = 1.0

    numMeshes = loadSequenceFromMeshFiles(_object, _directory, _filePrefix)

    _object.mesh_sequence_settings.numMeshes = numMeshes + 1
    _object.mesh_sequence_settings.numMeshesInMemory = numMeshes

    # set the speed back to its previous value
    _object.mesh_sequence_settings.speed = originalSpeed

    return numMeshes


def getMeshFromIndex(_obj, idx):
    key = _obj.mesh_sequence_settings.meshNameArray[idx].key
    return bpy.data.meshes[key]


def getMeshPropFromIndex(obj, idx):
    return obj.mesh_sequence_settings.meshNameArray[idx]


def setFrameNumber(frameNum):
    for obj in bpy.data.objects:
        if obj.mesh_sequence_settings.initialized is True and obj.mesh_sequence_settings.loaded is True:
            cacheMode = int(obj.mesh_sequence_settings.cacheMode)
            if cacheMode == 0:
                setFrameObj(obj, frameNum)
            elif cacheMode == 1:
                setFrameObjStreamed(obj, frameNum)


def getMeshIdxFromFrameNumber(_obj, frameNum):
    numFrames = _obj.mesh_sequence_settings.numMeshes - 1
    # convert the frame number into an array index
    idx = frameNum - (_obj.mesh_sequence_settings.startFrame - 1)
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


def setFrameObj(_obj, frameNum):
    # store the current mesh for grabbing the material later
    prev_mesh = _obj.data
    idx = getMeshIdxFromFrameNumber(_obj, frameNum)
    next_mesh = getMeshFromIndex(_obj, idx)

    if (next_mesh != prev_mesh):
        # swap the meshes
        _obj.data = next_mesh

        if _obj.mesh_sequence_settings.perFrameMaterial is False:
            # if the previous mesh had a material, copy it to the new one
            if(len(prev_mesh.materials) > 0):
                _obj.data.materials.clear()
                for material in prev_mesh.materials:
                    _obj.data.materials.append(material)


def setFrameObjStreamed(obj, frameNum):
    mss = obj.mesh_sequence_settings
    idx = getMeshIdxFromFrameNumber(obj, frameNum)
    nextMeshProp = getMeshPropFromIndex(obj, idx)

    # if we want to load new meshes as needed and it's not already loaded
    if nextMeshProp.inMemory is False and mss.streamDuringPlayback is True:
        # load the mesh into memory
        importStreamedFile(obj, idx)

    # if the mesh is in memory, show it
    if nextMeshProp.inMemory is True:
        next_mesh = getMeshFromIndex(obj, idx)

        # store the current mesh for grabbing the material later
        prev_mesh = obj.data
        if next_mesh != prev_mesh:
            # swap the old one with the new one
            obj.data = next_mesh

            # if we need to, copy the materials from the old one onto the new one
            if obj.mesh_sequence_settings.perFrameMaterial is False:
                if len(prev_mesh.materials) > 0:
                    obj.data.materials.clear()
                    for material in prev_mesh.materials:
                        obj.data.materials.append(material)

    # TODO: remove meshes until you're down to the cachSize (e.g. if you have 10 meshes in memory and you changed your cache size to 5)
    if mss.cacheSize > 0 and mss.numMeshesInMemory > mss.cacheSize:
        # find and delete the one closest to the end of the array
        idxToDelete = len(mss.meshNameArray) - 1
        while idxToDelete > 0 and (idxToDelete is idx or mss.meshNameArray[idxToDelete].inMemory is False):
            idxToDelete -= 1

        if idxToDelete >= 0:
            removeMeshFromCache(obj, idxToDelete)


# This function will be called from within both the Editor context and the Render context
# Keep that in mind when using bpy.context
def importStreamedFile(obj, idx):
    mss = obj.mesh_sequence_settings
    absDirectory = bpy.path.abspath(mss.dirPath)
    importFunc = importFuncFromTypeNumber(int(mss.fileFormat))
    filename = os.path.join(absDirectory, mss.meshNameArray[idx].basename)
    deselectAll()
    importFunc(filepath=filename)
    tmpObject = getSelectedObjects()[0]
    tmpMesh = tmpObject.data
    tmpMesh.use_fake_user = True
    tmpMesh.inMeshSequence = True
    deselectAll()
    tmpObject.select_set(state=True)
    # TODO: I don't think this bpy.ops.object.delete() works in render mode/locked interface mode
    bpy.ops.object.delete()
    mss.meshNameArray[idx].key = tmpMesh.name
    mss.meshNameArray[idx].inMemory = True
    mss.numMeshesInMemory += 1
    return tmpMesh


def removeMeshFromCache(obj, idx):
    mss = obj.mesh_sequence_settings
    meshKey = mss.meshNameArray[idx].key
    bpy.data.meshes.remove(bpy.data.meshes[meshKey])
    mss.meshNameArray[idx].inMemory = False
    mss.meshNameArray[idx].key = ''
    mss.numMeshesInMemory -= 1


def shadeSequence(_obj, smooth):
    deselectAll()
    _obj.select_set(state=True)
    # grab the current mesh so we can put it back later
    origMesh = _obj.data
    for idx in range(1, _obj.mesh_sequence_settings.numMeshes):
        _obj.data = getMeshFromIndex(_obj, idx)
        if(smooth):
            bpy.ops.object.shade_smooth()
        else:
            bpy.ops.object.shade_flat()
    # reset the sequence's mesh to the right one based on the current frame
    _obj.data = origMesh


def bakeSequence(_obj):
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

    meshNameElements = _obj.mesh_sequence_settings.meshNameArray
    # for each mesh (including the empty mesh):
    for meshName in meshNameElements:
        currentMesh = bpy.data.meshes[meshName.key]
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
        objMaterials = bpy.data.meshes[meshNameElements[1].name].materials
        meshesIter = iter(meshNameElements)
        # skip the emptyMesh
        next(meshesIter)
        # skip the first mesh (we'll copy the material from this one into the rest of them)
        next(meshesIter)
        for meshName in meshesIter:
            currentMesh = bpy.data.meshes[meshName.name]
            currentMesh.materials.clear()
            for material in objMaterials:
                currentMesh.materials.append(material)

    for frameNum in range(scn.frame_start, scn.frame_end + 1):
        # figure out which mesh is visible
        idx = getMeshIdxFromFrameNumber(_obj, frameNum)
        frameMesh = getMeshFromIndex(_obj, idx)

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


def freeUnusedMeshes():
    numFreed = 0
    for t_mesh in bpy.data.meshes:
        if t_mesh.inMeshSequence is True:
            t_mesh.use_fake_user = False
            numFreed += 1
    for t_obj in bpy.data.objects:
        if t_obj.mesh_sequence_settings.initialized is True and t_obj.mesh_sequence_settings.loaded is True:
            for t_meshName in t_obj.mesh_sequence_settings.meshNameArray:
                bpy.data.meshes[t_meshName.key].use_fake_user = True
                numFreed -= 1
    # the remaining meshes with no real or fake users will be garbage collected when Blender is closed
    print(numFreed, " meshes freed")


class AddMeshSequence(bpy.types.Operator):
    """Add Mesh Sequence"""
    # what the operator is called
    bl_idname = "ms.add_mesh_sequence"
    # what shows up in the menu
    bl_label = "Mesh Sequence"
    bl_options = {'UNDO'}

    def execute(self, context):
        newMeshSequence()
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
        obj = context.object
        dirPath = obj.mesh_sequence_settings.dirPath
        fileName = obj.mesh_sequence_settings.fileName

        meshCount = 0
        cacheModeNum = int(obj.mesh_sequence_settings.cacheMode)

        # cached
        if cacheModeNum == 0:
            meshCount = loadSequenceFromMeshFiles(obj, dirPath, fileName)

        # streaming
        elif cacheModeNum == 1:
            meshCount = loadStreamedSequenceFromMeshFiles(obj, dirPath, fileName)

        if meshCount == 0:
            self.report({'ERROR'}, "No matching files found. Make sure the Root Folder, File Name, and File Format are correct.")
            return {'CANCELLED'}

        return {'FINISHED'}


class ReloadMeshSequence(bpy.types.Operator):
    """Reload From Disk"""
    bl_idname = "ms.reload_mesh_sequence"
    bl_label = "Reload From Disk"
    bl_options = {'UNDO'}

    def execute(self, context):
        obj = context.object
        dirPath = obj.mesh_sequence_settings.dirPath
        fileName = obj.mesh_sequence_settings.fileName

        num = reloadSequenceFromMeshFiles(obj, dirPath, fileName)
        if num == 0:
            self.report({'ERROR'}, "Invalid file path. Make sure the Root Folder, File Name, and File Format are correct.")
            return {'CANCELLED'}

        return {'FINISHED'}


class BatchShadeSmooth(bpy.types.Operator):
    """Smooth Shade Sequence"""
    bl_idname = "ms.batch_shade_smooth"
    bl_label = "Smooth"
    bl_options = {'UNDO'}

    def execute(self, context):
        obj = context.object
        # True for smooth
        shadeSequence(obj, True)
        return {'FINISHED'}


class BatchShadeFlat(bpy.types.Operator):
    """Flat Shade Sequence"""
    bl_idname = "ms.batch_shade_flat"
    bl_label = "Flat"
    bl_options = {'UNDO'}

    def execute(self, context):
        obj = context.object
        # False for flat
        shadeSequence(obj, False)
        return {'FINISHED'}


class BakeMeshSequence(bpy.types.Operator):
    """Bake Mesh Sequence"""
    bl_idname = "ms.bake_sequence"
    bl_label = "Bake Mesh Sequence"
    bl_options = {'UNDO'}

    def execute(self, context):
        obj = context.object
        bakeSequence(obj)
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

                if objSettings.cacheMode == '0':
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

                elif objSettings.cacheMode == '1':
                    row = layout.row()
                    row.prop(objSettings, "cacheSize")

                    row = layout.row()
                    row.prop(objSettings, "streamDuringPlayback")
