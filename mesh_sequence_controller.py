bl_info = {
    "name" : "Stop motion OBJ",
    "description": "Import a sequence of OBJ files and display them each as a single frame of animation",
    "author": "Justin Jensen",
    "version": (0, 1),
    "blender": (2, 77, 0),
    "location": "View 3D > Add > Mesh > OBJ Sequence",
    "warning": "",
    "category": "Add Mesh"
}

import bpy
import os
import glob
from bpy.app.handlers import persistent

#global variable for the MeshSequenceController
MSC = None

#set the frame number for all mesh sequence objects
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
    #firstNum = bpy.props.IntProperty()
    #lastNum = bpy.props.IntProperty()
    #numFrames = bpy.props.IntProperty()
    startFrame = bpy.props.IntProperty(
        name='Start Frame',
        update=updateStartFrame,
        default=1)
    meshNames = bpy.props.StringProperty()
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
    
    #playback speed
    speed = bpy.props.FloatProperty(
        name='Playback Speed',
        min=0.0001,
        soft_min=0.01,
        step=25,
        precision=2,
        default=1
    )

class MeshSequence:
    """This class contains a reference to a sequence object as well as all of the meshes in the sequence"""
    
    bl_idname = "mesh_sequence_controller"
    bl_label = "Store and control animation of a mesh sequence"
    
    def __init__(self):
        #an array of meshes in the sequence
        self.meshes = []
        #create an empty mesh
        emptyMesh = bpy.data.meshes.new('emptyMesh')
        self.meshes.append(emptyMesh)
        #create a new object containing the empty mesh
        self.seqObject = bpy.data.objects.new("sequence", self.meshes[0])
        #link the object to the scene
        scn = bpy.context.scene
        scn.objects.link(self.seqObject)
        
        #deselect all other objects
        for ob in scn.objects:
            ob.select = False
        
        #select the object
        scn.objects.active = self.seqObject
        self.seqObject.select = True
        
        #set some defaults
        #self.firstNum = -1
        #self.lastNum = -1
        #self.numFrames = -1
        self.startFrame = 1
        self.meshNames = ''
        
        self.seqObject.mesh_sequence_settings.initialized = True
        
        
    
    def loadSequenceFromFile(self, _dir, _file):
        scn = bpy.context.scene
        #add a custom text property to the sequence object
        self.seqObject.mesh_sequence_settings.meshNames = ''
        #combine the file directory with the filename and the .obj extension
        full_filepath = os.path.join(_dir, _file + '*.obj')
        #print(full_filepath)
        numFrames = 0
        #for each file that matches the glob query:
        for file in glob.glob(full_filepath):
            #import the OBJ file
            bpy.ops.import_scene.obj(filepath = file)
            #get a reference to it
            tmpObject = bpy.context.selected_objects[0]
            #make a copy of the object's mesh and give it a fake user (so it doesn't get deleted)
            tmpMesh = tmpObject.data.copy()
            tmpMesh.use_fake_user = True
            #add its mesh to the meshes list
            self.meshes.append(tmpMesh)
            #select the object
            tmpObject.select = True
            #delete it
            bpy.ops.object.delete()
            #add the new mesh's name to the sequence object's text property
            #add the '/' character as a delimiter
            #http://stackoverflow.com/questions/1976007/what-characters-are-forbidden-in-windows-and-linux-directory-names
            self.seqObject.mesh_sequence_settings.meshNames += tmpMesh.name + '/'
            numFrames+=1
            
        if(numFrames > 0):
            #remove the last '/' from the string
            self.seqObject.mesh_sequence_settings.meshNames = self.seqObject.mesh_sequence_settings.meshNames[:-1]
            
            #set the sequence object's mesh to meshes[1]
            self.seqObject.data = self.meshes[1]
            #set the object's:
            #firstNum
            #self.firstNum = self.seqObject.mesh_sequence_settings.firstNum = _first
            #lastNum
            #self.lastNum = self.seqObject.mesh_sequence_settings.lastNum = _last
            #numFrames
            #self.numFrames = self.seqObject.mesh_sequence_settings.numFrames = _last - _first
            #startFrame
            self.startFrame = self.seqObject.mesh_sequence_settings.startFrame = 1
            
            #select the sequence object
            scn.objects.active = self.seqObject
            self.seqObject.select = True
            
            self.seqObject.mesh_sequence_settings.loaded = True
        
        return numFrames
    
    #this is used when a mesh sequence object has been saved and subsequently found in a .blend file
    def loadSequenceFromData(self, _object):
        scn = bpy.context.scene
        oldName = self.seqObject.name
        #assign _object to self
        self.seqObject = _object
        #get the object's custom properties:
        #firstNum
        #self.firstNum = _object.mesh_sequence_settings.firstNum
        #lastNum
        #self.lastNum = _object.mesh_sequence_settings.lastNum
        #numFrames
        #self.numFrames = _object.mesh_sequence_settings.numFrames
        #startFrame
        self.startFrame = _object.mesh_sequence_settings.startFrame
        #list of meshes
        self.meshNames = _object.mesh_sequence_settings.meshNames
        #split meshNames into individual mesh names
        #for each mesh
        for meshName in self.meshNames.split('/'):
            #add it to self.meshes
            self.meshes.append(bpy.data.meshes[meshName])
        
        #deselect all objects (otherwise everything that is selected will get deleted)
        for ob in scn.objects:
            ob.select = False
            
        #select and delete the empty object and empty mesh that __init__ created
        scn.objects.active = bpy.data.objects[oldName]
        bpy.data.objects[oldName].select = True
        bpy.ops.object.delete()
        
        #select the sequence object
        scn.objects.active = self.seqObject
        self.seqObject.select = True
        #set the frame number
        self.setFrame(scn.frame_current)
        
        self.seqObject.mesh_sequence_settings.loaded = True
        
        
    def setStartFrame(self, _frameNum):
        self.startFrame = _frameNum
        
    
    def getMeshIdxFromFrame(self, _frameNum):
        numFrames = len(self.meshes) - 1
        #convert the frame number into an array index
        idx = _frameNum - (self.seqObject.mesh_sequence_settings.startFrame - 1)
        #adjust for playback speed
        idx = int(idx * self.seqObject.mesh_sequence_settings.speed)
        #get the playback mode
        frameMode = int(self.seqObject.mesh_sequence_settings.frameMode)
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
    
    def setFrame(self, _frameNum):
        idx = self.getMeshIdxFromFrame(_frameNum)
        #store the current mesh for grabbing the material later
        prev_mesh = self.seqObject.data
        #swap the meshes
        self.seqObject.data = self.meshes[idx]
        #if the previous mesh had a material, copy it to the new one
        if(len(prev_mesh.materials) > 0):
            prev_material = prev_mesh.materials[0]
            self.seqObject.data.materials.clear()
            self.seqObject.data.materials.append(prev_material)
        
    def freeMeshes(self):
        #for each mesh
        for mesh in self.meshes:
            #remove the fake user from the mesh
            mesh.use_fake_user = False
    
    #create a separate object for each mesh in the array, each visible for only one frame
    def bakeSequence(self, context):
        #create an empty object and name it "C_{object's current name}" ('C' stands for 'Container')
        #copy the object's transformation data into the container
        #copy the object's animation data into the container
        
        #create a dictionary mapping meshes to new objects, meshToObject
        #create a placeholder for the object's material, objMaterial
        
        #for each mesh (including the empty mesh):
            #create an object for the mesh
            #remove the fake user from the mesh
            #if the mesh has a material, store this in objMaterial
            #add a dictionary entry to meshToObject, the mesh => the object
            #in the object, add keyframes at frames 0 and the last frame of the animation:
                #set object.hide to True
                #set object.hide_render to True
        
        #if objMaterial was set:
            #for each mesh:
                #set the material to objMaterial
        
        #for each frame of the animation:
            #figure out which mesh is visible
            #use the dictionary to find which object the mesh belongs to
            #add two keyframes to the object at the current frame:
                #set object.hide to False
                #set object.hide_render to False
            #add two keyframes to the object at the next frame:
                #set object.hide to True
                #set object.hide_render to True
        
        #delete the sequence object
        pass

class MeshSequenceController:
    
    def __init__(self):
        self.sequences = []
        #for each object in bpy.data.objects:
        for obj in bpy.data.objects:
        #for obj in bpy.context.scene.objects:
            #if it's a sequence object (we'll have to figure out how to indicate this, probably with a T/F custom property)
            if(obj.mesh_sequence_settings.initialized == True):
                #create a MeshSequence object for it
                tmpSeq = MeshSequence()
                #call sequence.loadSequenceFromData() on it
                tmpSeq.loadSequenceFromData(obj)
                self.sequences.append(tmpSeq)
            #else:
                #print("I'm NOT: " + obj.name)
        
    
    def setFrame(self, _frame):
        #check for deleted objects:
        #get all objects in the scene
        objs = bpy.data.objects.values()
        #for each mesh sequence
        for seq in self.sequences:
            #if its sequence object is not in the scene
            if (seq.seqObject in objs) == False:
                #free the object's meshes
                seq.freeMeshes()
                #remove the object from the sequence array
                #print('removing: ' + seq.seqObject.name)
                self.sequences.remove(seq)
        
        #for each sequence object:
        for obj in self.sequences:
            #call object.setFrame(_frame)
            obj.setFrame(_frame)

    def append(self, _obj):
        self.sequences.append(_obj)

    def remove(self, _obj):
        self.sequences.remove(_obj)
        #TODO: clear out the object's meshes
    
    def findMSOfromObject(self, _obj):
        for MSO in self.sequences:
            if MSO.seqObject == _obj:
                return MSO
    
    def cleanupExtraMeshes(self):
        #TODO
        #get every mesh in the scene and set use_fake_user to False
        #then go through every object in the sequences array and give their meshes fake users
        pass

@persistent
def initSequenceController(dummy):	#apparently we need a dummy variable?
    #print("initSequenceController was just called")
    global MSC
    #create a new MeshSequenceController object
    MSC = MeshSequenceController()


#Add mesh sequence operator
class AddMeshSequence(bpy.types.Operator):
    """Add OBJ Sequence"""
    #what the operator is called
    bl_idname = "ms.add_mesh_sequence"
    #what shows up in the menu
    bl_label = "OBJ Sequence"
    bl_options = {'UNDO'}

    def execute(self, context):
        #create a new MeshSequence object
        tmpMSO = MeshSequence()
        #add it to the MeshSequenceController, MSC
        global MSC
        MSC.append(tmpMSO)
        
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(AddMeshSequence.bl_idname, icon="PLUGIN")

class LoadMeshSequence(bpy.types.Operator):
    """Load OBJ Sequence"""
    bl_idname = "ms.load_mesh_sequence"
    bl_label = "Load OBJ Sequence"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        global MSC
        obj = context.object
        #get the object's file path
        dirPath = obj.mesh_sequence_settings.dirPath
        #get the object's filename
        fileName = obj.mesh_sequence_settings.fileName
        #find the MeshSequence object that contains this object
        MSO = MSC.findMSOfromObject(obj)
        
        num = MSO.loadSequenceFromFile(dirPath, fileName)
        if(num == 0):
            self.report({'ERROR'}, "Invalid file path. Please enter a Root Folder and File Name. Make sure to uncheck 'Relative Path'")
            return {'CANCELLED'}
        
        #print("We've loaded the OBJ sequence!")
        #print("Dirpath: " + dirPath)
        #print("filename: " + fileName)
        #print("MSO object name: " + MSO.seqObject.name)
        return {'FINISHED'}

class MeshSequencePanel(bpy.types.Panel):
    bl_idname = 'OBJ_SEQUENCE_properties'
    bl_label = 'OBJ Sequence'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    #bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        obj = context.object

        objSettings = obj.mesh_sequence_settings
        if(objSettings.initialized == True):
            if(objSettings.loaded == False):
                #path to directory
                row = layout.row()
                row.prop(objSettings, "dirPath")
                
                #filename
                row = layout.row()
                row.prop(objSettings, "fileName")
                
                #button for loading
                row = layout.row()
                row.operator("ms.load_mesh_sequence")
            
            #start frame
            row = layout.row()
            row.prop(objSettings, "startFrame")
            
            #frame mode
            row = layout.row()
            row.prop(objSettings, "frameMode")
            
            #playback speed
            row = layout.row()
            row.prop(objSettings, "speed")
    
def register():
    #print("Registered the OBJ Sequence addon")
    #register this settings class
    bpy.utils.register_class(MeshSequenceSettings)
    #add this settings class to bpy.types.Object
    bpy.types.Object.mesh_sequence_settings = bpy.props.PointerProperty(type=MeshSequenceSettings)
    bpy.app.handlers.load_post.append(initSequenceController)
    bpy.app.handlers.frame_change_pre.append(updateFrame)
    bpy.utils.register_class(AddMeshSequence)
    bpy.utils.register_class(LoadMeshSequence)
    bpy.utils.register_class(MeshSequencePanel)
    bpy.types.INFO_MT_mesh_add.append(menu_func)

def unregister():
    #print("Unregistered the OBJ Sequence addon")
    bpy.app.handlers.load_post.remove(initSequenceController)
    bpy.app.handlers.frame_change_pre.remove(updateFrame)
    bpy.utils.unregister_class(AddMeshSequence)
    bpy.utils.unregister_class(LoadMeshSequence)
    bpy.utils.unregister_class(MeshSequencePanel)
    bpy.types.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()