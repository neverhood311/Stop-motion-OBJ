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

from .stop_motion_obj import *

bl_info = {
    "name": "Stop motion OBJ",
    "description": "Import a sequence of OBJ (or STL or PLY) files and display them each as a single frame of animation. This add-on also supports the .STL and .PLY file formats.",
    "author": "Justin Jensen",
    "version": (2, 0, 2, "alpha.4"),
    "blender": (2, 80, 0),
    "location": "View 3D > Add > Mesh > Mesh Sequence",
    "warning": "",
    "category": "Add Mesh",
    "wiki_url": "https://github.com/neverhood311/Stop-motion-OBJ",
    "tracker_url": "https://github.com/neverhood311/Stop-motion-OBJ/issues"
}


def register():
    bpy.types.Mesh.inMeshSequence = bpy.props.BoolProperty()
    bpy.utils.register_class(MeshNameProp)
    bpy.utils.register_class(MeshSequenceSettings)
    bpy.types.Object.mesh_sequence_settings = bpy.props.PointerProperty(type=MeshSequenceSettings)
    bpy.app.handlers.load_post.append(initializeSequences)
    bpy.app.handlers.frame_change_pre.append(updateFrame)
    bpy.utils.register_class(AddMeshSequence)
    bpy.utils.register_class(LoadMeshSequence)
    bpy.utils.register_class(ReloadMeshSequence)
    bpy.utils.register_class(BatchShadeSmooth)
    bpy.utils.register_class(BatchShadeFlat)
    bpy.utils.register_class(BakeMeshSequence)
    bpy.utils.register_class(MeshSequencePanel)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)
    bpy.app.handlers.render_init.append(renderInitHandler)
    bpy.app.handlers.render_complete.append(renderCompleteHandler)
    bpy.app.handlers.render_cancel.append(renderCancelHandler)
    # TODO: can we use atexit to detect the program closing and cleanup meshes?
    #   otherwise, we might want a button to let the user clear the cache before saving the file


def unregister():
    bpy.app.handlers.load_post.remove(initializeSequences)
    bpy.app.handlers.frame_change_pre.remove(updateFrame)
    bpy.app.handlers.render_init.remove(renderInitHandler)
    bpy.app.handlers.render_complete.remove(renderCompleteHandler)
    bpy.app.handlers.render_cancel.remove(renderCancelHandler)
    bpy.utils.unregister_class(AddMeshSequence)
    bpy.utils.unregister_class(LoadMeshSequence)
    bpy.utils.unregister_class(ReloadMeshSequence)
    bpy.utils.unregister_class(BatchShadeSmooth)
    bpy.utils.unregister_class(BatchShadeFlat)
    bpy.utils.unregister_class(BakeMeshSequence)
    bpy.utils.unregister_class(MeshSequencePanel)
    bpy.utils.unregister_class(MeshSequenceSettings)
    bpy.utils.unregister_class(MeshNameProp)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)


if __name__ == "__main__":
    register()
