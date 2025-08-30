# Stop Motion OBJ - Manual Testing Instructions

This is mainly for my own benefit but including this with the repository couldn't hurt and it seemed like an appropriate place for this to live.

The goal is to have a repeatable (manual) test script that covers all major features without too much repeated work. Tests should be clear and easy to follow and all expected results should be clearly stated and easy to verify. No test should require the tester to find or create mesh sequences. Tests should be performed on only example sequences found within the repository.

## Main features that must be tested

- File import UI
- Each file type loads properly
- Import multiple sequences at once
- Cached sequences load, play, and render
- Streaming sequences load, play, and render
- Manual sequence creation
- Playback modes
- Auto-export (cached, streaming, overwrite vs new location)
- Advanced settings
  - Shading mode
  - Merge duplicate materials
  - Bake, Reload, Delete sequence
  - Sequence metadata
- Undo/Redo support
- Custom render loop
- Rendering with Cycles and Eevee
- Blender versions
  - At least the latest version and the latest LTS version
  - Optionally all feature versions from the first to the latest


# The tests

## Test 1
### Basic usage test for Cached sequences, all file types

1. File > Import > Mesh Sequence then navigate to "numbers_obj" folder 
1. In the `File Name` field, type "number", leave `Cache Mode` set to Cached, leave `Material Per Frame` unchecked and `Relative Paths` checked. Click `Select Folder` to load.
1. Repeat steps 1 & 2 for STL, PLY, and X3D (make sure the X3D I/O addon is installed). Once imported, translate each sequence slightly so they're not overlapping.
1. Step through frames 1-12
    - **CHECK**: all sequences should show the mesh corresponding to the frame number
1. In Object Settings > Stop Motion OBJ > Playback, set the `Mode` to Blank for one sequence.
    - **CHECK**: on frames 0 and 13, the sequence should disappear
1. Now set the playback `Mode` to Extend.
    - **CHECK**: on frame 0, the sequence should show a 1 and on frame 13 the sequence should show a 12
1. Now set the playback `Mode` to Repeat.
    - **CHECK**: on frame 0, the sequence should show a 12 and on frame 13 the sequence should show a 1
1. Now set the playback `Mode` to Bounce.
    - **CHECK**: on frame 13, the sequence should show a 12 then on each subsequent frame it should count down to 1 on frame 24. Frame 25 should also show a 1.
1. Now change the `Speed` to 0.5 and the playback `Mode` to Extend.
    - **CHECK**: on frame 2, the sequence should show a 1 and on frame 3 and 4, the sequence should show a 2
1. Now change the `Speed` to 2.0.
    - **CHECK**: on frame 1, the sequence should show a 1. On frame 2, the sequence should show a 3. On frame 3, the sequence should show a 5.
1. Now change the `Speed` back to 1.0 and change the `Start Frame` to 2 (`Mode` should still be set to Extend).
    - **CHECK**: on frames 1 and 2, the sequence should show a 1. On frame 12, the sequence should show an 11. On frame 13, the sequence should show a 12.
1. Set the `Start Frame` back to 1.
1. In Object Settings > Advanced > Shading, click `Smooth`.
    - **CHECK**: step through all frames and make sure that the meshes have smoothed faces
1. Now change the Shading to `Flat`.
    - **CHECK**: step through all frames and make sure that the meshes have flat faces
1. Now click `Bake Sequence`.
    - **CHECK**: the mesh sequence should have been converted to an empty object with all meshes as objects. Stop Motion OBJ settings shouldn't appear for the empty object.
    - **CHECK**: step through all frames and make sure that the mesh sequence is properly progressing.
    - **CHECK**: render the first 12 frames of the sequence at low quality settings and make sure the sequence is advancing in the rendered images. There should be one mesh displayed at a time.
1. Undo the `Bake Sequence`.
    - **CHECK**: make sure the baked sequence has been converted back into a mesh sequence and that Stop Motion OBJ settings are visible again.
1. Now click `Reload From Disk` on numbers_obj_sequence.
    - **CHECK**: the mesh sequence should still be visible and the shading should have reverted to Smooth shading (that's the indicator that the files have been reloaded).
1. Now click `Delete Sequence`. In Blender's `Outliner` panel, change the `Display Mode` from View Layer to Blender File.
    - **CHECK**: Under Meshes, there should be no meshes for the deleted mesh sequence.
    - **CHECK**: Under Objects, there should be no mesh sequence object.
1. Undo the `Delete Sequence`.
    - **CHECK**: the mesh sequence should reappear and sequence playback should behave as expected.
1. In the bottom of Stop Motion OBJ > Advanced, read the sequence metadata.
    - **CHECK**: Sequence Size should be 12
    - **CHECK**: Mesh directory should be correct
    - **CHECK**: Sequence version should be correct
1. Save the sequence to disk, close Blender, reopen Blender, and reload the saved file
    - **CHECK**: the mesh sequences should progress as expected.

## Test 2
### Basic usage test for Streaming sequences
1. File > Import > Mesh Sequence then navigate to "numbers_obj" folder 
1. In the `File Name` field, type "number", set `Cache Mode` to Streaming, leave `Material Per Frame` unchecked and `Relative Paths` checked. Click `Select Folder` to load.
    - **CHECK**: Frame 1 should be visible.
1. In Stop Motion OBJ > Advanced, read the sequence metadata.
    - **CHECK**: Sequence Size should be 12
    - **CHECK**: Cached meshes should be 1
1. In Blender's `Outliner` panel, change the `Display Mode` from View Layer to Blender File
    - **CHECK**: Under Meshes, you should see only two meshes: `emptyMesh` and `number_obj_1`
1. Advance to frame 2.
    - **CHECK**: Frame 2 should be visible.
    - **CHECK**: Cached meshes should be 2
    - **CHECK**: In the Outliner Panel > Current File > Meshes, you should see three meshes: `emptyMesh`, `number_obj_1`, and `number_obj_2`
1. In Stop Motion OBJ > Streaming, change `Cache size` to 1
    - **CHECK**: Frame 2 should still be visible
    - **CHECK**: Cached meshes should be 1
    - **CHECK**: In the Outliner Panel > Current File > Meshes, you should see only two meshes: `emptyMesh` and `number_obj_2`
1. Step through the animation from frame 1 to frame 12.
    - **CHECK**: you should see each mesh corresponding to the frame number
1. Render the first 12 frames of the sequence at low quality settings.
    - **CHECK**: the sequence should be advancing in the rendered images. There should be one mesh displayed at a time.
1. In Stop Motion OBJ > Advanced > Shading, click Smooth.
    - **CHECK**: step through the 12 frames of the sequence and make sure all meshes are smooth.
1. Now change the shading mode to Flat.
    - **CHECK**: step through the 12 frames of the sequence and make sure all meshes are flat.
1. Now click `Delete Sequence`. In Blender's `Outliner` panel, change the `Display Mode` from View Layer to Blender File.
    - **CHECK**: Under Meshes, there should be no meshes for the deleted mesh sequence.
    - **CHECK**: Under Objects, there should be no mesh sequence object.
1. Undo the `Delete Sequence`.
    - **CHECK**: the mesh sequence should reappear and sequence playback should behave as expected.
1. In Stop Motion OBJ > Streaming, uncheck Stream During Playback.
    - **CHECK**: step through the 12 frames of the sequence. Only the one that was most recently-loaded should be visible.
1. Save the sequence to disk, close Blender, reopen Blender, and reload the saved file
    - **CHECK**: the mesh sequence should progress as expected.

## Test 3
### Create mesh sequence manually
1. Add a box to the scene
1. Click Object > Convert to Mesh Sequence. Re-select the object
    - **CHECK**: Go to Object Settings > Stop Motion OBJ. Make sure the standard settings for a Cached mesh sequence are there.
    - **CHECK**: Look at the Timeline Editor. Make sure there's a keyframe set on the current frame.
    - **CHECK**: In Stop Motion OBJ > Playback, make sure the Playback Mode is set to Keyframe and there's an Active Mesh keyframe set for mesh #1.
1. Advance to frame 2 then click Stop Motion OBJ > Advanced > Duplicate Mesh Frame.
    - **CHECK**: In the Timeline Editor, there should be a new keyframe on frame 2.
    - **CHECK**: In Stop Motion OBJ > Playback, there should be an Active Mesh keyframe set for mesh #2.
    - **CHECK**: In Blender's Outliner, in the View Layer mode, expand Cube_sequence. The mesh listed should be `Cube.001`.
1. In Blender's `Outliner` panel, change the `Display Mode` from View Layer to Blender File
    - **CHECK**: Under Meshes, you should see three meshes: `emptyMesh`, `Cube`, and `Cube.001`.
1. Switch to Edit Mode, modify the mesh on frame 2, then switch back to Object Mode.
1. Advance to frame 3 then do the hotkey `Ctrl + Shift + D`.
    - **CHECK**: In the Timeline Editor, there should be a new keyframe on frame 3.
    - **CHECK**: In Stop Motion OBJ > Playback, there should be an Active Mesh keyframe set for mesh #3. This mesh should be identical to mesh #2, but different from mesh #1.
    - **CHECK**: In Blender's Outliner panel, under Meshes, you should see four meshes: `emptyMesh`, `Cube`, `Cube.001`, and `Cube.002`.
    - **CHECK**: In Blender's Outliner, in the View Layer mode, expand Cube_sequence. The mesh listed should be `Cube.002`.
1. Advance to frame 5 then do `Ctrl + Shift + D`. Then advance to frame 4 and do `Ctrl + Shift + D`.
    - **CHECK**: frame 4 should have `Cube.004` visible, which is Active Mesh 5.
    - **CHECK**: frame 5 should have `Cube.003` visible, which is Active Mesh 4.
1. Render the sequence using fast settings.
    - **CHECK**: make sure that the renders show the correct meshes in the right order.
1. Bake the sequence
    - **CHECK**: make sure that the sequence progresses properly
1. Undo the `Bake Sequence`
    - **CHECK**: make sure the baked sequence has been converted back into a mesh sequence and that Stop Motion OBJ settings are visible again.
1. Now click `Delete Sequence`. In Blender's `Outliner` panel, change the `Display Mode` from View Layer to Blender File.
    - **CHECK**: Under Meshes, there should be no meshes for the deleted mesh sequence.
    - **CHECK**: Under Objects, there should be no mesh sequence object.
1. Undo the `Delete Sequence`.
    - **CHECK**: the mesh sequence should reappear and sequence playback should behave as expected.
1. Save the sequence to disk, close Blender, reopen Blender, and reload the saved file
    - **CHECK**: the mesh sequence should progress as expected.

## Test 4
### Auto-export tests
1. Make a copy of the numbers_obj sequence to work on
1. File > Import > Mesh Sequence then navigate to "numbers_obj Copy" folder 
1. In the `File Name` field, type "number", set `Cache Mode` to Streaming, leave `Material Per Frame` unchecked and `Relative Paths` checked. Click `Select Folder` to load.
1. In Object Settings > Stop Motion OBJ > Export, enable Auto-export changes
1. Click on the Folder icon next to Export Folder. In the file dialog, create a new folder inside the sequence folder, open the folder, and click Accept.
1. Switch to Edit mode and move one vertex, then switch back to Object mode. Advance to frame 2.
    - **CHECK**: the Info panel on the bottom should say that mesh 1 was exported to the new folder.
    - **CHECK**: there should be a mesh 1 in the new folder.
1. Switch to Scupt mode and make some change. Advance to frame 3 (without leaving Sculpt mode).
    - **CHECK**: the Info panel on the bottom should say that mesh 2 was exported to the new folder.
    - **CHECK**: there should be a mesh 2 in the new folder.
1. Advance to frame 4 without making changes
    - **CHECK**: the Info panel on the bottom shouldn't have changed.
    - **CHECK**: there should NOT be a file for mesh 3.
1. In Object Settings > Stop Motion OBJ > Export, enable Overwrite Source.
1. Switch to Edit mode and move one vertex, then switch back to Object mode. Advance to frame 5.
    - **CHECK**: the Info panel on the bottom should say that a mesh was exported to the original folder.
    - **CHECK**: mesh 4 in the original folder should have a new timestamp.
1. Switch to Scupt mode and make some change. Advance to frame 6 (without leaving Sculpt mode).
    - **CHECK**: the Info panel on the bottom should say that a mesh was exported to the original folder.
    - **CHECK**: mesh 5 in the original folder should have a new timestamp.
1. Advance to frame 7 without making changes
    - **CHECK**: the Info panel on the bottom shouldn't have changed.
    - **CHECK**: the file for mesh 6 should not have a new timestamp.
1. In Object Settings > Stop Motion OBJ > Export, disable Auto-export changes.
1. Switch to Edit mode and move one vertex, then switch back to Object mode. Advance to frame 8.
    - **CHECK**: the Info panel on the bottom shouldn't have changed.
    - **CHECK**: mesh 7 shouldn't have been updated on disk.
1. Finally, repeat all of these steps for Cached sequences

## Test 5
### Keyframe playback mode
1. Load the numbers_obj sequence and just kind of play around with Keyframe playback mode.
    - **CHECK**: just make sure it looks right
    - **CHECK**: also make sure the frame updates in realtime while moving keyframes around in the graph editor

## Test 6
### Import multiple sequences at once
1. File > Import > Mesh Sequence then navigate to "examples" folder (where all the mesh sequence folders are located). 
1. In the `File Name` field, type "numbers_obj/number;horse_gallop/horse", leave `Cache Mode` set to Cached, leave `Material Per Frame` unchecked and `Relative Paths` checked. Click `Select Folder` to load.
1. Step through frames 1-24.
    - **CHECK**: Both sequences should progress as expected. The "numbers" sequence should stop on frame 12.
1. Repeat the test, but for Streaming Mode.