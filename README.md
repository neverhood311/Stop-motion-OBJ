# Stop-motion-OBJ
A Blender add-on for importing a sequence of OBJ meshes as frames

Stop motion OBJ allows you to import a sequence of OBJ files and render them as individual frames. Have a RealFlow animation but want to render it in Blender? This addon is for you! Currently tested for Blender 2.77.1.

### Features
- OBJ sequence import
- Allows changing topology 
  - (the OBJ files don't need to have the same number of vertices and faces)
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
- Only OBJ files are supported, as implied by the addon's name
- Doesn't work with physics

## Installing Stop motion OBJ
- Download mesh_sequence_controller.py and move it to Blender's addons folder (something like C:\Program Files\Blender Foundation\Blender\2.77\scripts\addons)
- Open Blender and open the Add-ons preferences (File > User Preferences... > Add-ons)
- In the search bar, type 'OBJ' and look for the Stop motion OBJ addon in the list
- Check the box to install it, and click 'Save User Settings'
- **RESTART BLENDER BEFORE USING THE ADDON**

## Using Stop motion OBJ
- (make sure you've installed the addon and restarted Blender before using)
- In the 3D view, click Add > Mesh > OBJ Sequence
  - The object will initially be empty. We need to load an OBJ sequence into it.
- Make sure the object is selected. 
- In the properties panel, click on the Object Properties tab (the little orange cube icon). In the settings panel, scroll down to find the OBJ Sequence subpanel and open it.
- Enter the Root Folder by clicking on the folder button and navigating to the folder where the OBJs are stored. **Make sure to UNCHECK ‘Relative Path’**
- In the File Name box, enter the common prefix of the OBJ files.
  - ex: If you have frame001, frame002, frame003, you should enter ‘frame’
- Click ‘Load Mesh Sequence’ to load. 
  - Depending on the number of frames, this could take a while.
- Step through a few frames to see the animation.
- You can adjust which frame the animation starts on as well as its playback speed.
- You can also decide what happens before and after the OBJ sequence:
  - 'Blank' will simply make the object disappear
  - 'Extend' will freeze the first and last frames before and after the OBJ sequence, respectively
  - 'Repeat' will repeat the animation
  - 'Bounce' will play the animation in reverse once the sequence has finished