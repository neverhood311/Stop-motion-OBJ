# Stop-motion-OBJ
A Blender add-on for importing a sequence of meshes as frames

Stop motion OBJ allows you to import a sequence of OBJ (or STL or PLY) files and render them as individual frames. Have a RealFlow animation but want to render it in Blender? This addon is for you! Currently tested for Blender 2.77.1.

If you find this add-on helpful, please consider donating to support development:

Bitcoin wallet: 16Bbv5jmKJ2T3dqw2rbaiL6vsoZvyNvaU1

PayPal: https://www.paypal.me/justinj

### IMPORTANT
- File numbers must be zero-padded
  - Like this: file001, file002, file003
  - NOT like this: ~~file1, file2, file3~~
- You MUST restart Blender after enabling the add-on

### Features
- Supported formats: OBJ, STL, PLY
- Allows changing topology 
  - (the meshes don't need to have the same number of vertices and faces)
- Supports shapes with UVs and image textures
- Variable playback speed
- Multiple playback modes
- Object can have materials
- Bake sequence
  - This allows the sequence to be seen on other computers without installing the addon (in a renderfarm, for example)

### Limitations
- Only absolute filepaths are supported (for now)
- File numbers must be zero-padded
- No motion blur
- ~~Doesn't work with physics~~ 
  - (It actually works with rigid body physics. In Rigid Body Collisions set Shape to 'Mesh' and Source to 'Base')
- Only single-object files are supported
- ~~Sequences can't be duplicated (for now)~~
  - Sequences can now be duplicated, but they share a material. For a duplicate sequence with a different material, you have to re-import the sequence.

## Installing Stop motion OBJ
- Download mesh_sequence_controller.py and move it to Blender's addons folder (something like C:\Program Files\Blender Foundation\Blender\2.77\scripts\addons)
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
- Enter the Root Folder by clicking on the folder button and navigating to the folder where the mesh files are stored. **Make sure to UNCHECK ‘Relative Path’**
- In the File Name box, enter a common prefix of the files.
  - ex: If you have frame001, frame002, frame003, you could enter ‘frame’, 'fram', or even 'f'
- Click ‘Load Mesh Sequence’ to load. 
  - Depending on the number of frames, this could take a while.
- Step through a few frames to see the animation.
- You can adjust which frame the animation starts on as well as its playback speed.
- You can also decide what happens before and after the mesh sequence:
  - 'Blank' will simply make the object disappear
  - 'Extend' will freeze the first and last frames before and after the mesh sequence, respectively
  - 'Repeat' will repeat the animation
  - 'Bounce' will play the animation in reverse once the sequence has finished
