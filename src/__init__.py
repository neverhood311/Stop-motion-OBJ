# ##### BEGIN GPL LICENSE BLOCK #####
#
#   Stop motion OBJ: A Mesh sequence importer for Blender
#   Copyright (C) 2016-2025  Justin Jensen
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
    "description": "Import a sequence of OBJ (or STL or PLY or X3D or VRML2) files and display them each as a single frame of animation. This add-on also supports the .STL, .PLY, .X3D, and .WRL file formats.",
    "author": "Justin Jensen",
    "version": (2, 3, 0),
    "blender": (4, 0, 0),
    "location": "File > Import > Mesh Sequence",
    "warning": "",
    "category": "Import",
    "wiki_url": "https://github.com/neverhood311/Stop-motion-OBJ/wiki",
    "tracker_url": "https://github.com/neverhood311/Stop-motion-OBJ/issues"
}

SMOKeymaps = []

def register():
    # TODO jjensen: can we fail this function if the Blender version is insufficient?
    bpy.app.handlers.frame_change_pre.append(checkMeshChangesFrameChangePre)
    bpy.app.handlers.frame_change_post.append(checkMeshChangesFrameChangePost)

    # this is needed so that the mesh frame is updated when 'Active Mesh' keyframes are changed
    # also for when new keyframes are added to a manually-created mesh sequence
    bpy.app.handlers.depsgraph_update_pre.append(updateFrame)

    bpy.types.Mesh.inMeshSequence = bpy.props.BoolProperty()
    bpy.types.Mesh.meshHash = bpy.props.StringProperty()
    bpy.utils.register_class(SequenceVersion)
    bpy.utils.register_class(MeshIO)
    bpy.utils.register_class(MeshNameProp)
    bpy.utils.register_class(MeshSequenceSettings)
    bpy.types.Object.mesh_sequence_settings = bpy.props.PointerProperty(type=MeshSequenceSettings)
    bpy.app.handlers.load_post.append(initializeSequences)
    bpy.app.handlers.frame_change_pre.append(updateFrame)
    
    # note: Blender tends to crash in Rendered viewport mode if we set the depsgraph_update_post instead of depsgraph_update_pre
    bpy.utils.register_class(ReloadMeshSequence)
    bpy.utils.register_class(BatchShadeSmooth)
    bpy.utils.register_class(BatchShadeFlat)
    bpy.utils.register_class(BakeMeshSequence)
    bpy.utils.register_class(DeepDeleteSequence)
    bpy.utils.register_class(MergeDuplicateMaterials)
    bpy.utils.register_class(RenderAnimationSMO)
    bpy.utils.register_class(ConvertToMeshSequence)
    bpy.utils.register_class(DuplicateMeshFrame)
    bpy.utils.register_class(SMO_PT_MeshSequencePanel)
    # note: the order of the next few panels is the order they appear in the UI
    bpy.utils.register_class(SMO_PT_MeshSequencePlaybackPanel)
    bpy.utils.register_class(SMO_PT_MeshSequenceStreamingPanel)
    bpy.utils.register_class(SMO_PT_MeshSequenceExportPanel)
    bpy.utils.register_class(SMO_PT_MeshSequenceAdvancedPanel)
    bpy.utils.register_class(SMO_PT_MeshSequenceRenderPanel)
    bpy.app.handlers.render_init.append(renderInitHandler)
    bpy.app.handlers.render_complete.append(renderCompleteHandler)
    bpy.app.handlers.render_cancel.append(renderCancelHandler)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_sequence)
    bpy.types.TOPBAR_MT_render.append(menu_func_render_animation_SMO)
    bpy.types.VIEW3D_MT_object.append(menu_func_convert_to_sequence)



    # the order here is important since it is the order in which these sections will be drawn
    bpy.utils.register_class(SMO_PT_FileImportSettingsPanel)
    bpy.utils.register_class(SMO_PT_TransformSettingsPanel)
    bpy.utils.register_class(SMO_PT_SequenceImportSettingsPanel)
    bpy.utils.register_class(SequenceImportSettings)
    bpy.utils.register_class(ImportSequence)

    bpy.app.handlers.load_post.append(makeDirPathsRelative)
    bpy.app.handlers.save_pre.append(makeDirPathsRelative)

    keyConfig = bpy.context.window_manager.keyconfigs.addon
    if keyConfig:
        spaceTypes = [('3D View', 'VIEW_3D'), ('Dopesheet', 'DOPESHEET_EDITOR'), ('Graph Editor', 'GRAPH_EDITOR')]
        for spaceType in spaceTypes:
            keyMap = keyConfig.keymaps.new(name=spaceType[0], space_type=spaceType[1])
            keyMapItem = keyMap.keymap_items.new('ms.duplicate_mesh_frame', type='D', value='PRESS', shift=True, ctrl=True)
            SMOKeymaps.append((keyMap, keyMapItem))

def unregister():
    bpy.app.handlers.frame_change_pre.remove(checkMeshChangesFrameChangePre)
    bpy.app.handlers.frame_change_post.remove(checkMeshChangesFrameChangePost)

    bpy.app.handlers.depsgraph_update_pre.remove(updateFrame)

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
    bpy.utils.unregister_class(MergeDuplicateMaterials)
    bpy.utils.unregister_class(RenderAnimationSMO)
    bpy.utils.unregister_class(ConvertToMeshSequence)
    bpy.utils.unregister_class(DuplicateMeshFrame)
    bpy.utils.unregister_class(SMO_PT_MeshSequencePanel)
    bpy.utils.unregister_class(SMO_PT_MeshSequencePlaybackPanel)
    bpy.utils.unregister_class(SMO_PT_MeshSequenceStreamingPanel)
    bpy.utils.unregister_class(SMO_PT_MeshSequenceExportPanel)
    bpy.utils.unregister_class(SMO_PT_MeshSequenceAdvancedPanel)
    bpy.utils.unregister_class(SMO_PT_MeshSequenceRenderPanel)

    bpy.utils.unregister_class(MeshSequenceSettings)
    bpy.utils.unregister_class(MeshNameProp)

    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_sequence)
    bpy.types.TOPBAR_MT_render.remove(menu_func_render_animation_SMO)
    bpy.types.VIEW3D_MT_object.remove(menu_func_convert_to_sequence)
    bpy.utils.unregister_class(SMO_PT_FileImportSettingsPanel)
    bpy.utils.unregister_class(SMO_PT_TransformSettingsPanel)
    bpy.utils.unregister_class(SMO_PT_SequenceImportSettingsPanel)
    bpy.utils.unregister_class(MeshIO)
    bpy.utils.unregister_class(SequenceVersion)
    bpy.utils.unregister_class(SequenceImportSettings)

    # make sure you register any classes ImportSequence depends on before registering this
    bpy.utils.unregister_class(ImportSequence)

    bpy.app.handlers.load_post.remove(makeDirPathsRelative)
    bpy.app.handlers.save_pre.remove(makeDirPathsRelative)

    for km, kmi in SMOKeymaps:
        km.keymap_items.remove(kmi)
    SMOKeymaps.clear()

if __name__ == "__main__":
    register()
