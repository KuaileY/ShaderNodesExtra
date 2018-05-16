import bpy
import os
from glob import glob
from os import path
import re
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty, FloatVectorProperty, CollectionProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper
from ShaderNodeBase import ShaderNodeBase

class ShaderNodeTextures(ShaderNodeBase):

    bl_name='ShaderNodeTextures'
    bl_label='ShaderNodeTextures'
    bl_icon='NONE'


#Principled suffix tags Shamelessly snagged from Node Wranger
    base_color = StringProperty(
        name='Base Color',
        default='diffuse diff albedo base col color dif',
        description='Naming Components for Base Color maps')
    ambient_occlusion = StringProperty(
        name='Ambient Occlusion',
        default='ao ambient_occlusion ambientocclusion occlusion ambient ambocc',
        description='Naming Components for Ambient Occlusion maps')
    sss_color = StringProperty(
        name='Subsurface Color',
        default='sss subsurface',
        description='Naming Components for Subsurface Color maps')
    metallic = StringProperty(
        name='Metallic',
        default='metallic metalness metal mtl',
        description='Naming Components for metallness maps')
    specular = StringProperty(
        name='Specular',
        default='specularity specular spec spc',
        description='Naming Components for Specular maps')
    normal = StringProperty(
        name='Normal',
        default='normal nor nrm nrml norm',
        description='Naming Components for Normal maps')
    bump = StringProperty(
        name='Bump',
        default='bump bmp',
        description='Naming Components for bump maps')
    rough = StringProperty(
        name='Roughness',
        default='roughness rough rgh',
        description='Naming Components for roughness maps')
    gloss = StringProperty(
        name='Gloss',
        default='gloss glossy glossyness',
        description='Naming Components for glossy maps')
    displacement = StringProperty(
        name='Displacement',
        default='displacement displace disp dsp height heightmap',
        description='Naming Components for displacement maps')

    def updateFilePath(self, context):
        selectedfile = path.basename(self.filepath)
        directory = path.dirname(self.filepath)


        def get_matching_imgs(selectedfile, directory):
            files = []
            name = []
            dir_files = os.listdir(directory)
            for f in range(len(dir_files)):
                splitfile = path.splitext(dir_files[f])
                ext = splitfile[1]
                noext = splitfile[0]
                if ext in bpy.path.extensions_image:
                    files.append(dir_files[f])

            return files

        if selectedfile != self.bl_label:
            # print(selectedfile + ' not equal label of ' + self.bl_label) #debug
            files = get_matching_imgs(selectedfile, directory)
            # for i in files: #debug
            #     print(i)

            # Helper_functions
            def split_into__components(fname):
                # Split filename into components
                # 'WallTexture_diff_2k.002.jpg' -> ['Wall', 'Texture', 'diff', 'k']
                # Remove extension
                fname = path.splitext(fname)[0]
                # Remove digits
                fname = ''.join(i for i in fname if not i.isdigit())
                # Seperate CamelCase by space
                fname = re.sub("([a-z])([A-Z])","\g<1> \g<2>",fname)
                # Replace common separators with SPACE
                seperators = ['_', '.', '-', '__', '--', '#']
                for sep in seperators:
                    fname = fname.replace(sep, ' ')

                components = fname.split(' ')
                components = [c.lower() for c in components]
                return components

            # Filter textures names for texturetypes in filenames
            # [Socket Name, [abbreviations and keyword list], Filename placeholder]
            tags = self # bpy.context.user_preferences.addons['node_wrangler'].preferences.principled_tags
            normal_abbr = tags.normal.split(' ')
            bump_abbr = tags.bump.split(' ')
            gloss_abbr = tags.gloss.split(' ')
            rough_abbr = tags.rough.split(' ')
            socketnames = [
            ['Displacement', tags.displacement.split(' '), None],
            ['Base Color', tags.base_color.split(' '), None],
            ['AO', tags.ambient_occlusion.split(' '), None], #not in NW
            ['Subsurface Color', tags.sss_color.split(' '), None],
            ['Metallic', tags.metallic.split(' '), None],
            ['Specular', tags.specular.split(' '), None],
            ['Roughness', rough_abbr + gloss_abbr, None],
            ['Normal', normal_abbr + bump_abbr, None],
            ]

            # Look through texture_types and set value as filename of first matched file
            def match_files_to_socket_names():
                for sname in socketnames:
                    for file in range(len(files)):
                        fname = files[file]
                        filenamecomponents = split_into__components(fname)
                        matches = set(sname[1]).intersection(set(filenamecomponents))
                        # TODO: ignore basename (if texture is named "fancy_metal_nor", it will be detected as metallic map, not normal map)
                        if matches:
                            sname[2] = fname
                            break

            match_files_to_socket_names()
            # Remove socketnames without found files
            print(socketnames[2], directory)
            socketnames = [s for s in socketnames if s[2]
                           and path.exists(directory+os.sep+s[2])]
            if not socketnames:
                #self.report({'INFO'}, 'No matching images found')
                print('No matching images found')
                return None

            # Add found images
            print('\nMatched Textures:')
            texture_nodes = []
            disp_texture = None
            normal_node = None
            roughness_node = None
            for i, sname in enumerate(socketnames):
                print(i, sname[0], sname[2])

                # if self.node_tree.nodes[sname[0]].image != bpy.data.images[sname[2]]:
                #     # No texture node connected -> add texture node with new image
                #     texture_node = self.nodes[sname[0]]
                #     img = bpy.data.images.load(directory+os.sep+sname[2], check_existing=True)
                #     texture_node.image = img

                # DISPLACEMENT NODES
                if sname[0] == 'Displacement':
                    bpy.data.images.load(directory+os.sep+sname[2], check_existing=True)
                    self.node_tree.nodes[sname[0]].image = bpy.data.images[sname[2]]


                    continue



                    # NORMAL NODES
                    if sname[0] == 'Normal':
                        # Test if new texture node is normal or bump map
                        fname_components = split_into__components(sname[2])
                        match_normal = set(normal_abbr).intersection(set(fname_components))
                        match_bump = set(bump_abbr).intersection(set(fname_components))
                        if match_normal:
                            # If Normal add normal node in between
                            self.delLink('nodes["Bump"].outputs[0]', 'nodes["Group Output"].inputs[4]')
                            self.addLink('nodes["Normal"].outputs[0]', 'nodes["Group Output"].inputs[4]')
                            bpy.data.images.load(directory+os.sep+sname[2], check_existing=True)
                            self.node_tree.nodes[sname[0]].image = bpy.data.images[sname[2]]

                        elif match_bump:
                            # If Bump add bump node in between
                            self.delLink('nodes["Normal Map"].outputs[0]', 'nodes["Group Output"].inputs[4]')
                            self.addLink('nodes["Bump"].outputs[0]', 'nodes["Group Output"].inputs[4]')
                            bpy.data.images.load(directory+os.sep+sname[2], check_existing=True)
                            self.node_tree.nodes[sname[0]].image = bpy.data.images[sname[2]]

                        else:
                            continue


                    elif sname[0] == 'Roughness':
                        # Test if glossy or roughness map
                        fname_components = split_into__components(sname[2])
                        match_rough = set(rough_abbr).intersection(set(fname_components))
                        match_gloss = set(gloss_abbr).intersection(set(fname_components))

                        if match_rough:
                            # If Roughness nothing to to
                            self.addLink('nodes["Roughness"].outputs[0]', 'nodes["Group Output"].inputs[3]')
                            self.delLink('nodes["Invert"].outputs[0]', 'nodes["Group Output"].inputs[3]')
                            bpy.data.images.load(directory+os.sep+sname[2], check_existing=True)
                            self.node_tree.nodes[sname[0]].image = bpy.data.images[sname[2]]

                        elif match_gloss:
                            # If Gloss Map add invert node
                            self.delLink('nodes["Roughness"].outputs[0]', 'nodes["Group Output"].inputs[3]')
                            self.addLink('nodes["Invert"].outputs[0]', 'nodes["Group Output"].inputs[3]')
                            bpy.data.images.load(directory+os.sep+sname[2], check_existing=True)
                            self.node_tree.nodes[sname[0]].image = bpy.data.images[sname[2]]

                    else:
                        # This is a simple connection Texture --> Input slot
                        continue


                else:
                    bpy.data.images.load(directory+os.sep+sname[2], check_existing=True)
                    self.node_tree.nodes[sname[0]].image = bpy.data.images[sname[2]]
                    continue

                # This are all connected texture nodes
                # texture_nodes.append(texture_node)
                # texture_node.label = sname[0]

            # if disp_texture:
            #     texture_nodes.append(disp_texture)

            # for texture_node in texture_nodes:
            #     link = links.new(texture_node.inputs[0], group_input.outputs[0])

            # Just to be sure
            # active_node.select = False
            # nodes.update()
            # links.update()
            # force_update(context)
            # return {'FINISHED'}





    filepath = StringProperty(name="Maps DIR", description="image path", subtype="FILE_PATH", update=updateFilePath)

    def defaultNodeTree(self):
        self.addNode('ShaderNodeNormalMap', {'name':'Normal Map', 'inputs[0].default_value':1.000})
        self.addNode('ShaderNodeTexImage', {'name':'AO'})
        self.addNode('ShaderNodeTexImage', {'name':'Roughness', 'color_space':'NONE'})
        self.addNode('ShaderNodeTexImage', {'name':'Metallic', 'color_space':'NONE'})
        self.addNode('ShaderNodeTexImage', {'name':'Normal', 'color_space':'NONE'})
        self.addNode('ShaderNodeTexImage', {'name':'Displacement', 'color_space':'NONE'})
        self.addNode('ShaderNodeMath', {'name':'Displace Offset', 'operation':'SUBTRACT', 'use_clamp':0.000})
        self.addNode('ShaderNodeMath', {'name':'Displace Strength', 'operation':'MULTIPLY', 'use_clamp':0.000})
        self.addNode('ShaderNodeTexImage', {'name':'Base Color'})
        self.addNode('ShaderNodeBump', {'name':'Bump'})
        self.addNode('ShaderNodeInvert', {'name':'Invert'})
        self.addInput('NodeSocketVector', {'name':'Vector', 'default_value':[0.000,0.000,0.000], 'min_value':0.000, 'max_value':1.000})
        self.addInput('NodeSocketFloat', {'name':'Displace Offset', 'default_value':0.500, 'min_value':-10000.000, 'max_value':10000.000})
        self.addInput('NodeSocketFloat', {'name':'Displace Strength', 'default_value':1.000, 'min_value':-10000.000, 'max_value':10000.000})
        self.addOutput('NodeSocketColor', {'name':'Base Color', 'default_value':[0.000,0.000,0.000,0.000]})
        self.addOutput('NodeSocketColor', {'name':'AO', 'default_value':[0.000,0.000,0.000,0.000]})
        self.addOutput('NodeSocketColor', {'name':'Metallic', 'default_value':[0.000,0.000,0.000,0.000]})
        self.addOutput('NodeSocketColor', {'name':'Roughness', 'default_value':[0.000,0.000,0.000,0.000]})
        self.addOutput('NodeSocketVector', {'name':'Normal', 'default_value':[0.000,0.000,0.000], 'min_value':0.000, 'max_value':1.000})
        self.addOutput('NodeSocketFloat', {'name':'Displacement', 'default_value':0.000, 'min_value':0.000, 'max_value':0.000})
        self.addLink('nodes["Group Input"].outputs[0]', 'nodes["Base Color"].inputs[0]')
        self.addLink('nodes["Roughness"].outputs[0]', 'nodes["Group Output"].inputs[3]')
        self.addLink('nodes["Roughness"].outputs[0]', 'nodes["Invert"].inputs[1]')
        self.addLink('nodes["Metallic"].outputs[0]', 'nodes["Group Output"].inputs[2]')
        self.addLink('nodes["Group Input"].outputs[0]', 'nodes["Metallic"].inputs[0]')
        self.addLink('nodes["Group Input"].outputs[0]', 'nodes["Roughness"].inputs[0]')
        self.addLink('nodes["Group Input"].outputs[0]', 'nodes["Displacement"].inputs[0]')
        self.addLink('nodes["Group Input"].outputs[0]', 'nodes["Normal"].inputs[0]')
        self.addLink('nodes["Group Input"].outputs[0]', 'nodes["AO"].inputs[0]')
        self.addLink('nodes["Normal"].outputs[0]', 'nodes["Normal Map"].inputs[1]')
        self.addLink('nodes["Normal"].outputs[0]', 'nodes["Bump"].inputs[2]')
        self.addLink('nodes["Normal Map"].outputs[0]', 'nodes["Group Output"].inputs[4]')
        self.addLink('nodes["Base Color"].outputs[0]', 'nodes["Group Output"].inputs[0]')
        self.addLink('nodes["AO"].outputs[0]', 'nodes["Group Output"].inputs[1]')
        self.addLink('nodes["Displacement"].outputs[0]', 'nodes["Displace Offset"].inputs[0]')
        self.addLink('nodes["Group Input"].outputs[1]', 'nodes["Displace Offset"].inputs[1]')
        self.addLink('nodes["Displace Offset"].outputs[0]', 'nodes["Displace Strength"].inputs[0]')
        self.addLink('nodes["Displace Strength"].outputs[0]', 'nodes["Group Output"].inputs[5]')
        self.addLink('nodes["Group Input"].outputs[2]', 'nodes["Displace Strength"].inputs[1]')

    def init(self, context):
        self.width = 220
        self.setupTree()

    # def copy(self, node):
    #     self.node_tree=node.node_tree.copy()

    def free(self):
        if self.node_tree.users==1:
            bpy.data.node_groups.remove(self.node_tree, do_unlink=True)

    #def socket_value_update(self, context):

    #def update(self):

    def draw_buttons(self, context, layout):
        col=layout.column()
        col.prop(self, 'filepath', text="Base Color")

    #def draw_buttons_ext(self, contex, layout):

    def draw_label(self):
        node_label = path.basename(self.filepath)
        return node_label

    def draw_menu():
        return 'SH_NEW_TexTools' , 'Texture Group'
