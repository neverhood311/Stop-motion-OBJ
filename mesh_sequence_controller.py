# ##### BEGIN GPL LICENSE BLOCK #####
#
#   Stop motion OBJ: A Mesh sequence importer for Blender
#   Copyright (C) 2016-2018  Justin Jensen
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


bl_info = {
    "name" : "Stop motion OBJ",
    "description": "Import a sequence of OBJ (or STL or PLY) files and display them each as a single frame of animation. This add-on also supports the .STL and .PLY file formats.",
    "author": "Justin Jensen",
    "version": (0, 2),
    "blender": (2, 79, 0),
    "location": "View 3D > Add > Mesh > Mesh Sequence",
    "warning": "",
    "category": "Add Mesh",
    "wiki_url": "https://github.com/neverhood311/Stop-motion-OBJ",
    "tracker_url": "https://github.com/neverhood311/Stop-motion-OBJ/issues"
}

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

#global variable for the MeshSequenceController
MSC = None

def deselectAll():
    for ob in bpy.context.scene.objects:
        ob.select = False

#set the frame number for all mesh sequence objects
#COMMENT THIS persistent OUT WHEN RUNNING FROM THE TEXT EDITOR
@persistent
def updateFrame(dummy):
    scn = bpy.context.scene
    global MSC
    MSC.setFrame(scn.frame_current)

#runs every time the start frame of an object is changed
def updateStartFrame(self, context):
    updateFrame(0)
    return None
    
class MeshSequenceSettings(bpy.types.PropertyGroup):
    dirPath = bpy.props.StringProperty(
        name="Root Folder",
        description="Only .OBJ files will be listed",
        subtype="DIR_PATH")
    fileName = bpy.props.StringProperty(name='File Name')
    startFrame = bpy.props.IntProperty(
        name='Start Frame',
        update=updateStartFrame,
        default=1)
    #A long list of mesh names
    meshNames = bpy.props.StringProperty()
    numMeshes = bpy.props.IntProperty()
    initialized = bpy.props.BoolProperty(default=False)
    loaded = bpy.props.BoolProperty(default=False)
    
    #out-of-range frame mode
    frameMode = bpy.props.EnumProperty(
        items = [('0', 'Blank', 'Object disappears when frame is out of range'),
                ('1', 'Extend', 'First and last frames are duplicated'),
                ('2', 'Repeat', 'Repeat the animation'),
                ('3', 'Bounce', 'Play in reverse at the end of the frame range')],
        name='Frame Mode',
        default='1')
    
    #material mode (one material total or one material per frame)
    perFrameMaterial = bpy.props.BoolProperty(
        name='Material per Frame',
        default=False
    )
    
    #playback speed
    speed = bpy.props.FloatProperty(
        name='Playback Speed',
        min=0.0001,
        soft_min=0.01,
        step=25,
        precision=2,
        default=1
    )
    
    #the file format for files in the sequence (OBJ, STL, or PLY)
    fileFormat = bpy.props.EnumProperty(
        items = [('0', 'OBJ', 'Wavefront OBJ'),
                ('1', 'STL', 'STereoLithography'),
                ('2', 'PLY', 'Stanford PLY')],
        name='File Format',
        default='0')

class MeshSequenceController:
    
    def __init__(self):
        #for each object in bpy.data.objects:
        for obj in bpy.data.objects:
        #for obj in bpy.context.scene.objects:
            #if it's a sequence object (we'll have to figure out how to indicate this, probably with a T/F custom property)
            if(obj.mesh_sequence_settings.initialized == True):
                #call sequence.loadSequenceFromData() on it
                self.loadSequenceFromData(obj)
        self.freeUnusedMeshes()
        
    def newMeshSequence(self):
        #create an empty mesh
        emptyMesh = bpy.data.meshes.new('emptyMesh')
        #give it a fake user
        emptyMesh.use_fake_user = True
        #make sure it knows it's part of a mesh sequence
        emptyMesh.inMeshSequence = True
        #create a new object containing the empty mesh
        theObj = bpy.data.objects.new("sequence", emptyMesh)
        theObj.mesh_sequence_settings.meshNames = emptyMesh.name + '/'
        #link the object to the scene
        scn = bpy.context.scene
        scn.objects.link(theObj)
        
        #deselect all other objects
        deselectAll()
        
        #select the object
        scn.objects.active = theObj
        theObj.select = True
        
        theObj.mesh_sequence_settings.initialized = True
        return theObj
    
    def loadSequenceFromFile(self, _obj, _dir, _file):
        scn = bpy.context.scene
        #get the file format
        format = 'obj'
        formatidx = int(_obj.mesh_sequence_settings.fileFormat)
        importFunc = None
        #OBJ
        if(formatidx == 0):
            format = 'obj'
            importFunc = bpy.ops.import_scene.obj
        #STL
        elif(formatidx == 1):
            format = 'stl'
            importFunc = bpy.ops.import_mesh.stl
        #PLY
        elif(formatidx == 2):
            format = 'ply'
            importFunc = bpy.ops.import_mesh.ply
        #combine the file directory with the filename and the .obj extension
        full_dirpath = bpy.path.abspath(_dir)
        full_filepath = os.path.join(full_dirpath, _file + '*.' + format)

        numFrames = 0
        unsortedFiles = glob.glob(full_filepath)
        # Sort the given list in the way that humans expect.
        sortedFiles = sorted(unsortedFiles, key=alphanumKey)

        #for each file that matches the glob query:
        for file in sortedFiles:
            #import the mesh file
            importFunc(filepath = file)
            #get a reference to it
            tmpObject = bpy.context.selected_objects[0]
            tmpMesh = tmpObject.data    #don't copy it; just copy the pointer. This cuts memory usage in half.
            tmpMesh.use_fake_user = True
            tmpMesh.inMeshSequence = True
            #deselect all objects
            deselectAll()
            #select the object
            tmpObject.select = True
            #delete it
            bpy.ops.object.delete()
            #add the new mesh's name to the sequence object's text property
            #add the '/' character as a delimiter
            #http://stackoverflow.com/questions/1976007/what-characters-are-forbidden-in-windows-and-linux-directory-names
            _obj.mesh_sequence_settings.meshNames += tmpMesh.name + '/'
            numFrames+=1
        
        _obj.mesh_sequence_settings.numMeshes = numFrames+1
        if(numFrames > 0):
            #remove the last '/' from the string
            _obj.mesh_sequence_settings.meshNames = _obj.mesh_sequence_settings.meshNames[:-1]
            #set the sequence object's mesh to meshes[1]
            self.setFrameObj(_obj, scn.frame_current)
            
            #select the sequence object
            scn.objects.active = _obj
            _obj.select = True
            
            _obj.mesh_sequence_settings.loaded = True
        
        return numFrames
    
    #this is used when a mesh sequence object has been saved and subsequently found in a .blend file
    def loadSequenceFromData(self, _obj):
        scn = bpy.context.scene
        t_meshNames = _obj.mesh_sequence_settings.meshNames.split('/')
        #count the number of mesh names
        #(helps with backwards compatibility)
        _obj.mesh_sequence_settings.numMeshes = len(t_meshNames)
        
        #make sure the meshes know they're part of a mesh sequence
        #(helps with backwards compatibility)
        for t_meshName in t_meshNames:
            bpy.data.meshes[t_meshName].inMeshSequence = True
        
        #deselect all objects (otherwise everything that is selected will get deleted)
        deselectAll()
        
        #select the sequence object
        scn.objects.active = _obj
        _obj.select = True
        #set the frame number
        self.setFrameObj(_obj, scn.frame_current)
        
        _obj.mesh_sequence_settings.loaded = True
    
    def getMesh(self, _obj, _idx):
        #get the object's meshNames
        #split it into individual mesh names
        names = _obj.mesh_sequence_settings.meshNames.split('/')
        #return the one at _idx
        name = names[_idx]
        return bpy.data.meshes[name]
    
    def setFrame(self, _frame):
        #for each object in the scene
        for obj in bpy.data.objects:
            #if it's been loaded and initialized
            if obj.mesh_sequence_settings.initialized == True and obj.mesh_sequence_settings.loaded == True:
                #set the frame on the sequence object
                self.setFrameObj(obj, _frame)

    def getMeshIdxFromFrame(self, _obj, _frameNum):
        numFrames = _obj.mesh_sequence_settings.numMeshes - 1
        #convert the frame number into an array index
        idx = _frameNum - (_obj.mesh_sequence_settings.startFrame - 1)
        #adjust for playback speed
        idx = int(idx * _obj.mesh_sequence_settings.speed)
        #get the playback mode
        frameMode = int(_obj.mesh_sequence_settings.frameMode)
        #0: Blank
        if(frameMode == 0):
            if(idx < 1 or idx >= numFrames + 1):
                idx = 0
        #1: Extend (default)
        elif(frameMode == 1):
            if(idx < 1):
                idx = 1
            elif(idx >= numFrames + 1):
                idx = numFrames
        #2: Repeat
        elif(frameMode == 2):
            idx -= 1
            idx = idx % (numFrames)
            idx += 1
        #3: Bounce
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
        idx = self.getMeshIdxFromFrame(_obj, _frameNum)
        #store the current mesh for grabbing the material later
        prev_mesh = _obj.data
        #swap the meshes
        _obj.data = self.getMesh(_obj, idx)
        # If this object doesn't have materials for each frame
        if(_obj.mesh_sequence_settings.perFrameMaterial == False):
            #if the previous mesh had a material, copy it to the new one
            if(len(prev_mesh.materials) > 0):
                prev_material = prev_mesh.materials[0]
                _obj.data.materials.clear()
                _obj.data.materials.append(prev_material)
    
    #iterate over the meshes in the sequence and set their shading to smooth or flat
    def shadeSequence(self, _obj, _smooth):
        scn = bpy.context.scene
        #deselect everything in the scene
        deselectAll()
        #select the sequence object
        scn.objects.active = _obj
        _obj.select = True
        #grab the current mesh so we can put it back later
        origMesh = _obj.data
        #for each mesh in the sequence
        for idx in range(1, _obj.mesh_sequence_settings.numMeshes):
            #set the object's mesh to this mesh
            _obj.data = self.getMesh(_obj, idx)
            if(_smooth):
                #call Blender's shade_smooth operator
                bpy.ops.object.shade_smooth()
            else:
                #call Blender's shade_flat operator
                bpy.ops.object.shade_flat()
        #reset the sequence's mesh to the right one based on the current frame
        _obj.data = origMesh
        
    
    #create a separate object for each mesh in the array, each visible for only one frame
    def bakeSequence(self, _obj):
        scn = bpy.context.scene
        #create an empty object
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        containerObj = bpy.context.active_object
        #rename the container object to "C_{object's current name}" ('C' stands for 'Container')
        newName = "C_" + _obj.name
        containerObj.name = newName
        
        #copy the object's transformation data into the container
        containerObj.location = _obj.location
        containerObj.scale = _obj.scale
        containerObj.rotation_euler = _obj.rotation_euler
        containerObj.rotation_quaternion = _obj.rotation_quaternion   #just in case
        
        #copy the object's animation data into the container
        #http://blender.stackexchange.com/questions/27136/how-to-copy-keyframes-from-one-action-to-other
        if(_obj.animation_data != None):
            seq_anim = _obj.animation_data
            properties = [p.identifier for p in seq_anim.bl_rna.properties if not p.is_readonly]
            if(containerObj.animation_data == None):
                containerObj.animation_data_create()
            cont_anim = containerObj.animation_data
            for prop in properties:
                setattr(cont_anim, prop, getattr(seq_anim, prop))
        
        #create a dictionary mapping meshes to new objects, meshToObject
        meshToObject = {}
        
        meshNames = _obj.mesh_sequence_settings.meshNames.split('/')
        #for each mesh (including the empty mesh):
        for meshName in meshNames:
            mesh = bpy.data.meshes[meshName]
            #even though it's kinda still part of a mesh sequence, it's not really anymore
            mesh.inMeshSequence = False
            #create an object for the mesh and add it to the scene
            tmpObj = bpy.data.objects.new('o_' + mesh.name, mesh)
            scn.objects.link(tmpObj)
            #remove the fake user from the mesh
            mesh.use_fake_user = False
            #add a dictionary entry to meshToObject, the mesh => the object
            meshToObject[mesh] = tmpObj
            #in the object, add keyframes at frames 0 and the last frame of the animation:
            #set object.hide to True
            tmpObj.hide = True
            tmpObj.keyframe_insert(data_path='hide', frame=scn.frame_start)
            tmpObj.keyframe_insert(data_path='hide', frame=scn.frame_end)
            #set object.hide_render to True
            tmpObj.hide_render = True
            tmpObj.keyframe_insert(data_path='hide_render', frame=scn.frame_start)
            tmpObj.keyframe_insert(data_path='hide_render', frame=scn.frame_end)
            #set the empty object as this object's parent
            tmpObj.parent = containerObj
        
        #If this is a single-material sequence, make sure the material is copied to the whole sequence
        #This assumes that the first mesh in the sequence has a material
        if(_obj.mesh_sequence_settings.perFrameMaterial == False):
            #grab the materials from the first frame
            objMaterials = bpy.data.meshes[meshNames[1]].materials
            #for each mesh:
            iterMeshes = iter(meshNames)
            next(iterMeshes)    #skip the emptyMesh
            next(iterMeshes)    #skip the first mesh (we'll copy the material from this one into the rest of them)
            for meshName in iterMeshes:
                mesh = bpy.data.meshes[meshName]
                #set the material to objMaterial
                mesh.materials.clear()
                for material in objMaterials:
                    mesh.materials.append(material)
        
        #for each frame of the animation:
        for frameNum in range(scn.frame_start, scn.frame_end + 1):
            #figure out which mesh is visible
            idx = self.getMeshIdxFromFrame(_obj, frameNum)
            frameMesh = self.getMesh(_obj, idx)
            #use the dictionary to find which object the mesh belongs to
            frameObj = meshToObject[frameMesh]
            #add two keyframes to the object at the current frame:
            #set object.hide to False
            frameObj.hide = False
            frameObj.keyframe_insert(data_path='hide', frame=frameNum)
            #set object.hide_render to False
            frameObj.hide_render = False
            frameObj.keyframe_insert(data_path='hide_render', frame=frameNum)
            #add two keyframes to the object at the next frame:
            #set object.hide to True
            frameObj.hide = True
            frameObj.keyframe_insert(data_path='hide', frame=frameNum+1)
            #set object.hide_render to True
            frameObj.hide_render = True
            frameObj.keyframe_insert(data_path='hide_render', frame=frameNum+1)
        
        #delete the sequence object
        deselectAll()
        scn.objects.active = _obj
        _obj.select = True
        bpy.ops.object.delete()
    
    def freeUnusedMeshes(self):
        numFreed = 0
        #for every mesh in the scene
        for t_mesh in bpy.data.meshes:
            #if inMeshSequence is set to True
            if t_mesh.inMeshSequence == True:
                #set its use_fake_user to False
                t_mesh.use_fake_user = False
                numFreed += 1
        #for every object in the scene
        for t_obj in bpy.data.objects:
            #if its mesh sequence has been initialized and loaded
            if t_obj.mesh_sequence_settings.initialized == True and t_obj.mesh_sequence_settings.loaded == True:
                #get its meshNames
                t_meshNames = t_obj.mesh_sequence_settings.meshNames
                #for each mesh name
                for t_meshName in t_meshNames.split('/'):
                    #set its use_fake_user to True
                    bpy.data.meshes[t_meshName].use_fake_user = True
                    numFreed -= 1
        #the remaining meshes with no real or fake users will be garbage collected when Blender is closed
        print(numFreed, " meshes freed")

#COMMENT THIS persistent OUT WHEN RUNNING FROM THE TEXT EDITOR
@persistent
def initSequenceController(dummy):    #apparently we need a dummy variable?
    global MSC
    #create a new MeshSequenceController object
    MSC = MeshSequenceController()


#Add mesh sequence operator
class AddMeshSequence(bpy.types.Operator):
    """Add Mesh Sequence"""
    #what the operator is called
    bl_idname = "ms.add_mesh_sequence"
    #what shows up in the menu
    bl_label = "Mesh Sequence"
    bl_options = {'UNDO'}

    def execute(self, context):
        global MSC
        obj = MSC.newMeshSequence()
        
        return {'FINISHED'}

#the function for adding "Mesh Sequence" to the Add > Mesh menu
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
        #get the object's file path
        dirPath = obj.mesh_sequence_settings.dirPath
        #get the object's filename
        fileName = obj.mesh_sequence_settings.fileName
        
        num = MSC.loadSequenceFromFile(obj, dirPath, fileName)
        if(num == 0):
            self.report({'ERROR'}, "No matching files found. Make sure the Root Folder, File Name, and File Format are correct.")
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
        MSC.shadeSequence(obj, True)    #True for smooth
        return {'FINISHED'}

class BatchShadeFlat(bpy.types.Operator):
    """Flat Shade Sequence"""
    bl_idname = "ms.batch_shade_flat"
    bl_label = "Flat"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        global MSC
        obj = context.object
        MSC.shadeSequence(obj, False)   #False for flat
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
        #update the frame so the right shape is visible
        bpy.context.scene.frame_current = bpy.context.scene.frame_current
        return {'FINISHED'}

#The properties panel added to the Object Properties Panel list        
class MeshSequencePanel(bpy.types.Panel):
    bl_idname = 'OBJ_SEQUENCE_properties'
    bl_label = 'Mesh Sequence'   #The name that will show up in the properties panel
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    
    def draw(self, context):
        layout = self.layout
        obj = context.object

        objSettings = obj.mesh_sequence_settings
        if(objSettings.initialized == True):
            #Only show options for loading a sequence if one hasn't been loaded yet
            if(objSettings.loaded == False):
                layout.label("Load Mesh Sequence:", icon='FILE_FOLDER')
                #path to directory
                row = layout.row()
                row.prop(objSettings, "dirPath")
                
                #filename
                row = layout.row()
                row.prop(objSettings, "fileName")
                
                #file extension
                row = layout.row()
                row.prop(objSettings, "fileFormat")
                
                #material mode (one material total or one material per frame)
                row = layout.row()
                row.prop(objSettings, "perFrameMaterial")
                
                #button for loading
                row = layout.row()
                row.operator("ms.load_mesh_sequence")
                
            if(objSettings.loaded == True):
                #start frame
                row = layout.row()
                row.prop(objSettings, "startFrame")
                
                #frame mode
                row = layout.row()
                row.prop(objSettings, "frameMode")
                
                #playback speed
                row = layout.row()
                row.prop(objSettings, "speed")
                
                #Show the shading buttons only if a sequence has been loaded
                layout.row().separator()
                row = layout.row(align=True)
                row.label("Shading:")
                row.operator("ms.batch_shade_smooth")
                row.operator("ms.batch_shade_flat")
                
                #Bake Sequence button
                layout.row().separator()
                row = layout.row()
                box = row.box()
                box.operator("ms.bake_sequence")
    
def register():
    #give bpy.types.Mesh a new property that says whether it's part of a mesh sequence
    bpy.types.Mesh.inMeshSequence = bpy.props.BoolProperty()    #defaults to False
    #register this settings class
    bpy.utils.register_class(MeshSequenceSettings)
    #add this settings class to bpy.types.Object
    bpy.types.Object.mesh_sequence_settings = bpy.props.PointerProperty(type=MeshSequenceSettings)
    bpy.app.handlers.load_post.append(initSequenceController)
    bpy.app.handlers.frame_change_pre.append(updateFrame)
    bpy.utils.register_class(AddMeshSequence)
    bpy.utils.register_class(LoadMeshSequence)
    bpy.utils.register_class(BatchShadeSmooth)
    bpy.utils.register_class(BatchShadeFlat)
    bpy.utils.register_class(BakeMeshSequence)
    bpy.utils.register_class(MeshSequencePanel)
    bpy.types.INFO_MT_mesh_add.append(menu_func)
    #for running the script, instead of installing the add-on
    #UNCOMMENT THIS FUNCTION CALL WHEN RUNNING FROM THE TEXT EDITOR
    #initSequenceController(0)

def unregister():
    bpy.app.handlers.load_post.remove(initSequenceController)
    bpy.app.handlers.frame_change_pre.remove(updateFrame)
    bpy.utils.unregister_class(AddMeshSequence)
    bpy.utils.unregister_class(LoadMeshSequence)
    bpy.utils.unregister_class(BatchShadeSmooth)
    bpy.utils.unregister_class(BatchShadeFlat)
    bpy.utils.unregister_class(BakeMeshSequence)
    bpy.utils.unregister_class(MeshSequencePanel)
    bpy.types.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
