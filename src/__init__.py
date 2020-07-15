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
from .panels import *

bl_info = {
    "name": "Stop motion OBJ",
    "description": "Import a sequence of OBJ (or STL or PLY) files and display them each as a single frame of animation. This add-on also supports the .STL and .PLY file formats.",
    "author": "Justin Jensen",
    "version": (2, 1, 0, "beta.16"),
    "blender": (2, 80, 0),
    "location": "File > Import > Mesh Sequence",
    "warning": "",
    "category": "Import",
    "wiki_url": "https://github.com/neverhood311/Stop-motion-OBJ/wiki",
    "tracker_url": "https://github.com/neverhood311/Stop-motion-OBJ/issues"
}


def register():
    bpy.types.Mesh.inMeshSequence = bpy.props.BoolProperty()
    bpy.utils.register_class(SequenceVersion)
    bpy.utils.register_class(MeshImporter)
    bpy.utils.register_class(MeshNameProp)
    bpy.utils.register_class(MeshSequenceSettings)
    bpy.types.Object.mesh_sequence_settings = bpy.props.PointerProperty(type=MeshSequenceSettings)
    bpy.app.handlers.load_post.append(initializeSequences)
    bpy.app.handlers.frame_change_pre.append(updateFrame)
    bpy.utils.register_class(ReloadMeshSequence)
    bpy.utils.register_class(BatchShadeSmooth)
    bpy.utils.register_class(BatchShadeFlat)
    bpy.utils.register_class(BakeMeshSequence)
    bpy.utils.register_class(DeepDeleteSequence)
    bpy.utils.register_class(SMO_PT_MeshSequencePanel)
    bpy.utils.register_class(SMO_PT_MeshSequencePlaybackPanel)
    bpy.utils.register_class(SMO_PT_MeshSequenceStreamingPanel)
    bpy.utils.register_class(SMO_PT_MeshSequenceAdvancedPanel)
    bpy.app.handlers.render_init.append(renderInitHandler)
    bpy.app.handlers.render_complete.append(renderCompleteHandler)
    bpy.app.handlers.render_cancel.append(renderCancelHandler)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_sequence)

    # the order here is important since it is the order in which these sections will be drawn
    bpy.utils.register_class(SMO_PT_FileImportSettingsPanel)
    bpy.utils.register_class(SMO_PT_TransformSettingsPanel)
    bpy.utils.register_class(SMO_PT_SequenceImportSettingsPanel)
    bpy.utils.register_class(SequenceImportSettings)
    bpy.utils.register_class(ImportSequence)

    bpy.app.handlers.load_post.append(makeDirPathsRelative)
    bpy.app.handlers.save_pre.append(makeDirPathsRelative)


def unregister():
    bpy.app.handlers.load_post.remove(initializeSequences)
    bpy.app.handlers.frame_change_pre.remove(updateFrame)
    bpy.app.handlers.render_init.remove(renderInitHandler)
    bpy.app.handlers.render_complete.remove(renderCompleteHandler)
    bpy.app.handlers.render_cancel.remove(renderCancelHandler)
    bpy.utils.unregister_class(ReloadMeshSequence)
    bpy.utils.unregister_class(BatchShadeSmooth)
    bpy.utils.unregister_class(BatchShadeFlat)
    bpy.utils.unregister_class(BakeMeshSequence)
    bpy.utils.unregister_class(DeepDeleteSequence)
    bpy.utils.unregister_class(SMO_PT_MeshSequencePanel)
    bpy.utils.unregister_class(SMO_PT_MeshSequencePlaybackPanel)
    bpy.utils.unregister_class(SMO_PT_MeshSequenceStreamingPanel)
    bpy.utils.unregister_class(SMO_PT_MeshSequenceAdvancedPanel)
    bpy.utils.unregister_class(MeshSequenceSettings)
    bpy.utils.unregister_class(MeshNameProp)

    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_sequence)
    bpy.utils.unregister_class(SMO_PT_FileImportSettingsPanel)
    bpy.utils.unregister_class(SMO_PT_TransformSettingsPanel)
    bpy.utils.unregister_class(SMO_PT_SequenceImportSettingsPanel)
    bpy.utils.unregister_class(MeshImporter)
    bpy.utils.unregister_class(SequenceVersion)
    bpy.utils.unregister_class(SequenceImportSettings)

    # make sure you register any classes ImportSequence depends on before registering this
    bpy.utils.unregister_class(ImportSequence)

    bpy.app.handlers.load_post.remove(makeDirPathsRelative)
    bpy.app.handlers.save_pre.remove(makeDirPathsRelative)

if __name__ == "__main__":
    register()
