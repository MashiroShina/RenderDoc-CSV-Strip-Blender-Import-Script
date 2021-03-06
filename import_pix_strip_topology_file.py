# ##### BEGIN GPL LICENSE BLOCK #####
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

import bpy
import csv
import mathutils
from bpy_extras.io_utils import unpack_list, unpack_face_list, axis_conversion
from bpy.props import (BoolProperty,
                       FloatProperty,
                       StringProperty,
                       EnumProperty,
                       )
from collections import OrderedDict

bl_info = {
    "name": "PIX CSV Strip File",
    "author": "Stanislav Bobovych and Tommy Soucy",
    "version": (1, 0, 0),
    "blender": (2, 7, 8),
    "location": "File > Import-Export",
    "description": "Import PIX csv dump of mesh. Import mesh, normals and UVs. Assuming a Triangle Strip Primitive Topology",
    "category": "Import"}


class PIX_CSV_Operator(bpy.types.Operator):
    bl_idname = "object.pix_csv_importer"
    bl_label = "Import PIX csv Strip File"
    filepath = bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob = StringProperty(default="*.csv", options={'HIDDEN'})
    mirror_x = bpy.props.BoolProperty(name="Mirror X",
                                      description="Mirror all the vertices across X axis",
                                      default=True)
                                      
    vertex_order = bpy.props.BoolProperty(name="Change vertex order",
                                      description="Reorder vertices in counter-clockwise order",
                                      default=True)
    axis_forward = EnumProperty(
            name="Forward",
            items=(('X', "X Forward", ""),
                   ('Y', "Y Forward", ""),
                   ('Z', "Z Forward", ""),
                   ('-X', "-X Forward", ""),
                   ('-Y', "-Y Forward", ""),
                   ('-Z', "-Z Forward", ""),
                   ),
            default='Z')

    axis_up = EnumProperty(
            name="Up",
            items=(('X', "X Up", ""),
                   ('Y', "Y Up", ""),
                   ('Z', "Z Up", ""),
                   ('-X', "-X Up", ""),
                   ('-Y', "-Y Up", ""),
                   ('-Z', "-Z Up", ""),
                   ),
            default='Y',
                )

    def execute(self, context):
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob"))

        global_matrix = axis_conversion(from_forward=self.axis_forward,
                                        from_up=self.axis_up,
                                        ).to_4x4()
        keywords["global_matrix"] = global_matrix

        print(keywords)
        importCSV(**keywords)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text="Import options")

        row = col.row()
        row.prop(self, "mirror_x")
        row = col.row()
        row.prop(self, "vertex_order")
        layout.prop(self, "axis_forward")
        layout.prop(self, "axis_up")


def make_mesh(verteces, faces, normals, uvs, global_matrix):
    mesh = bpy.data.meshes.new('name')
    mesh.vertices.add(len(verteces))
    mesh.vertices.foreach_set("co", unpack_list(verteces))
    mesh.tessfaces.add(len(faces))
    mesh.tessfaces.foreach_set("vertices_raw", unpack_face_list(faces))

    index = 0
    for vertex in mesh.vertices:
        vertex.normal = normals[index]
        index += 1

    uvtex = mesh.tessface_uv_textures.new()
    uvtex.name = "UV"

    for face, uv in enumerate(uvs):
        data = uvtex.data[face]
        data.uv1 = uv[0]
        data.uv2 = uv[1]
        data.uv3 = uv[2]
    mesh.update(calc_tessface=False, calc_edges=False)

    obj = bpy.data.objects.new('name', mesh)
    # apply transformation matrix
    obj.matrix_world = global_matrix
    bpy.context.scene.objects.link(obj)  # link object to scene


def importCSV(filepath=None, mirror_x=False, vertex_order=True, global_matrix=None):
    if global_matrix is None:
        global_matrix = mathutils.Matrix()

    if filepath == None:
        return
    vertex_dict = {}
    normal_dict = {}

    vertices = []
    faces = []
    normals = []
    uvs = []

    with open(filepath) as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        vert_count = sum(1 for row in reader)

        f.seek(0)
        reader = csv.reader(f)
        next(reader)  # skip header

        current_face = []
        current_uv = []
        x_mod = 1
        if mirror_x:
            x_mod = -1
                
        # this is where begins my work, the rest of this script isn't mine
        ################################## build vertices, triangles (faces), normals, and uvs array ###########################
            
        i=1
        j=0
        previous_vertex1=None
        previous_vertex2=None
        while i<vert_count:
            #here we access the data from the CSV file directly, which is very slow, we have to access previous lines which means iterating through all previous lines twice every 3 vertices
            #the print statement is to make sure the sript is actually running
            print("processing vertex #"+str(i))
            f.seek(0)
            reader = csv.reader(f)
            for k in range(i):
                f.readline()
            current_vertex=next(reader)
            if j==3:
                j=0
                #########make triangle with previous data in special order and current
                
                #previous_vertex2 goes before previous_vertex1 in this "special order"
                
                #first tri vert
                vertex_index = int(previous_vertex2[0])
                vertex_dict[vertex_index] = (x_mod*float(previous_vertex2[2]), float(previous_vertex2[3]), float(previous_vertex2[4]))
                normal_dict[vertex_index] = (float(previous_vertex2[6]), float(previous_vertex2[7]), float(previous_vertex2[8]))
                uv = (float(previous_vertex2[9]), 1.0 - float(previous_vertex2[10]))
                current_face.append(vertex_index)
                current_uv.append(uv)
                
                #second tri vert
                vertex_index = int(previous_vertex1[0])
                vertex_dict[vertex_index] = (x_mod*float(previous_vertex1[2]), float(previous_vertex1[3]), float(previous_vertex1[4]))
                normal_dict[vertex_index] = (float(previous_vertex1[6]), float(previous_vertex1[7]), float(previous_vertex1[8]))
                uv = (float(previous_vertex1[9]), 1.0 - float(previous_vertex1[10]))
                current_face.append(vertex_index)
                current_uv.append(uv)
                
                #third tri vert
                vertex_index = int(current_vertex[0])
                vertex_dict[vertex_index] = (x_mod*float(current_vertex[2]), float(current_vertex[3]), float(current_vertex[4]))
                normal_dict[vertex_index] = (float(current_vertex[6]), float(current_vertex[7]), float(current_vertex[8]))
                uv = (float(current_vertex[9]), 1.0 - float(current_vertex[10]))
                current_face.append(vertex_index)
                if vertex_order:
                    faces.append((current_face[2], current_face[1], current_face[0]))
                else:
                    faces.append(current_face)
                current_uv.append(uv)
                uvs.append(current_uv)
                current_face = []
                current_uv = []
                
                #########
                i-=1
            elif j==2:
                j+=1
                #########make triangle with previous data and current
                
                #first tri vert
                vertex_index = int(previous_vertex1[0])
                vertex_dict[vertex_index] = (x_mod*float(previous_vertex1[2]), float(previous_vertex1[3]), float(previous_vertex1[4]))
                normal_dict[vertex_index] = (float(previous_vertex1[6]), float(previous_vertex1[7]), float(previous_vertex1[8]))
                uv = (float(previous_vertex1[9]), 1.0 - float(previous_vertex1[10]))
                current_face.append(vertex_index)
                current_uv.append(uv)
                
                #second tri vert
                vertex_index = int(previous_vertex2[0])
                vertex_dict[vertex_index] = (x_mod*float(previous_vertex2[2]), float(previous_vertex2[3]), float(previous_vertex2[4]))
                normal_dict[vertex_index] = (float(previous_vertex2[6]), float(previous_vertex2[7]), float(previous_vertex2[8]))
                uv = (float(previous_vertex2[9]), 1.0 - float(previous_vertex2[10]))
                current_face.append(vertex_index)
                current_uv.append(uv)
                
                #third tri vert
                vertex_index = int(current_vertex[0])
                vertex_dict[vertex_index] = (x_mod*float(current_vertex[2]), float(current_vertex[3]), float(current_vertex[4]))
                normal_dict[vertex_index] = (float(current_vertex[6]), float(current_vertex[7]), float(current_vertex[8]))
                uv = (float(current_vertex[9]), 1.0 - float(current_vertex[10]))
                current_face.append(vertex_index)
                if vertex_order:
                    faces.append((current_face[2], current_face[1], current_face[0]))
                else:
                    faces.append(current_face)
                current_uv.append(uv)
                uvs.append(current_uv)
                current_face = []
                current_uv = []
                
                #########
                
                previous_vertex1=previous_vertex2
                previous_vertex2=current_vertex
                
                i+=1
            else:
                j+=1
                previous_vertex1=previous_vertex2
                previous_vertex2=current_vertex
                i+=1
                                
        ###############################
        # this is where ends my work
        
        for i in range(len(vertex_dict)):
            if i in vertex_dict:
                pass
            else:
    #            print("missing",i)
                vertex_dict[i] = (0, 0, 0)
                normal_dict[i] = (0, 0, 0)

        # dictionary sorted by key
        vertex_dict = OrderedDict(sorted(vertex_dict.items(), key=lambda t: t[0]))
        normal_dict = OrderedDict(sorted(normal_dict.items(), key=lambda t: t[0]))

        for key in vertex_dict:
            vertices.append(list(vertex_dict[key]))
    #        print(key,vertex_dict[key])
        for key in normal_dict:
            normals.append(list(normal_dict[key]))

    #    print(vertices)
    #    print(faces)
    #    print(normals)
    #    print(uvs)
        make_mesh(vertices, faces, normals, uvs, global_matrix)


def menu_func_import(self, context):
    self.layout.operator(PIX_CSV_Operator.bl_idname, text="PIX CSV Strip File (.csv)")


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
#    register()
#    These run the script from "Run script" button
    bpy.utils.register_class(PIX_CSV_Operator)
    bpy.ops.object.pix_csv_importer('INVOKE_DEFAULT')