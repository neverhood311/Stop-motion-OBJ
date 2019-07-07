# Stop-motion-OBJ
A Blender add-on for importing a sequence of meshes as frames

Stop motion OBJ allows you to import a sequence of OBJ (or STL or PLY) files and render them as individual frames. Have a RealFlow animation but want to render it in Blender? This addon is for you! There are now two versions:
- [v2.0.0](https://github.com/neverhood311/Stop-motion-OBJ/releases/tag/v2.0.0) for **Blender 2.80+**
- [r1.1.1](https://github.com/neverhood311/Stop-motion-OBJ/releases/tag/0.2.79.2) for Blender 2.79 (also tested for 2.77 and 2.78). This version is now deprecated and will no longer be supported

If you find this add-on helpful, please consider donating to support development:

Bitcoin wallet: 16Bbv5jmKJ2T3dqw2rbaiL6vsoZvyNvaU1

PayPal: https://www.paypal.me/justinj

### IMPORTANT
- You MUST restart Blender after enabling the add-on

### Features
- Supported formats: OBJ, STL, PLY
- Allows changing topology 
  - (the meshes don't need to have the same number of vertices and faces)
- Supports shapes with UVs and image textures
- Variable playback speed
- Multiple playback modes
- Reload from disk
  - If you change your mesh sequence, you can reload the sequence into the existing object without deleting it and creating a new one
- Object can have different materials on each frame
  - For instance, you can have a different MTL file for each OBJ file
- Bake sequence
  - This allows the sequence to be viewed on other computers without installing the addon (in a renderfarm, for example)

### Limitations
- No motion blur
- Only single-object files are supported
- ~~Only absolute filepaths are supported~~
  - Fixed in [https://github.com/neverhood311/Stop-motion-OBJ/pull/17](https://github.com/neverhood311/Stop-motion-OBJ/pull/17)
- ~~File numbers must be zero-padded~~
  - Sorting file with correct order is added in [this PR](https://github.com/neverhood311/Stop-motion-OBJ/pull/15)
  - Files like file1, file2, file3 will be loaded in correct order, and zero-padded filenames still work, too.
- ~~Doesn't work with physics~~ 
  - (It actually works with rigid body physics. In Rigid Body Collisions set Shape to 'Mesh' and Source to 'Base')
- ~~Sequences can't be duplicated~~
  - Sequences can now be duplicated, but they share a material. For a duplicate sequence with a different material, you have to re-import the sequence.

## Installing Stop motion OBJ
- Download mesh_sequence_controller.py and move it to Blender's addons folder (something like C:\Program Files\Blender Foundation\Blender\2.80\scripts\addons)
- Open Blender and open the Add-ons preferences (File > User Preferences... > Add-ons)
- In the search bar, type 'OBJ' and look for the Stop motion OBJ addon in the list
- Check the box to install it, and click 'Save User Settings'
- **RESTART BLENDER BEFORE USING THE ADDON**

## Using Stop motion OBJ
- (make sure you've installed the addon and restarted Blender before using)
- In the 3D view, click Add > Mesh > Mesh Sequence
  - The object will initially be empty. We need to load a mesh sequence into it.
- Make sure the object is selected.
- In the properties panel, click on the Object Properties tab (the little orange cube icon). In the settings panel, scroll down to find the Mesh Sequence subpanel and open it.
- Enter the Root Folder by clicking on the folder button and navigating to the folder where the mesh files are stored. ~~**Make sure to UNCHECK ‘Relative Path’**~~
- In the File Name box, enter a common prefix of the files.
  - ex: If you have frame001, frame002, frame003, you could enter ‘frame’, 'fram', or even 'f'
- If your sequence has a different material for each frame, check the "Material per Frame" checkbox. Otherwise, leave it unchecked.
- Click ‘Load Mesh Sequence’ to load. 
  - Depending on the number of frames, this could take a while.
- Step through a few frames to see the animation.
- You can adjust which frame the animation starts on as well as its playback speed.
- You can also decide what happens before and after the mesh sequence:
  - 'Blank' will simply make the object disappear after the end of the sequence
  - 'Extend' will freeze the first and last frames before and after the mesh sequence, respectively
  - 'Repeat' will repeat the animation
  - 'Bounce' will play the animation in reverse once the sequence has finished
- Once your sequence is loaded, you can change the shading (smooth or flat) of the entire sequence:
  - The shading buttons are found in the Mesh Sequence Settings for the object
  - Note: The normal shading buttons (in the 3D View "Tools" panel) will only affect the current frame, not the entire sequence
- If you change your mesh sequence and want to reload it without creating a new sequence object, click 'Reload From Disk'
  - This will use the original Root Folder and File Name that you initially specified
  - If your updated sequence has more or fewer frames than the original one, the updated sequence object will reflect this change