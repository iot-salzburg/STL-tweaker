#!/usr/bin/env python3.4
# Author: Christoph Schranz, Salzburg Research

import sys, os
import struct
import time
import zipfile
import xml.etree.ElementTree as ET


class FileHandler:
    def __init__(self, inputfile):
        return None
        
    def loadMesh(inputfile):
        '''load meshs and object attributes from file'''
        ## loading mesh format
        
        filetype = os.path.splitext(inputfile)[1].lower()
        if filetype == ".stl":
            f=open(inputfile,"rb")
            if "solid" in str(f.read(5).lower()):
                f=open(inputfile,"r")
                mesh=FileHandler.loadAsciiSTL(f)
                if len(mesh) < 3:
                     f.seek(5, os.SEEK_SET)
                     mesh=FileHandler.loadBinarySTL(f)
            else:
                mesh=FileHandler.loadBinarySTL(f)
                
        elif filetype == ".3mf":
            objs = FileHandler.load3mf(inputfile)
            mesh = objs[0][0]
        else:
            print("File type is not supported.")
            sys.exit()
            
        return mesh


    def loadAsciiSTL(f):
        '''Reading mesh data from ascii STL'''
        mesh=list()
        for line in f:
            if "vertex" in line:
                data=line.split()[1:]
                mesh.append([float(data[0]), float(data[1]), float(data[2])])
        return mesh

    def loadBinarySTL(f):
        '''Reading mesh data from binary STL'''
        	#Skip the header
        f.read(80-5)
        faceCount = struct.unpack('<I', f.read(4))[0]
        mesh=list()
        for idx in range(0, faceCount):
            data = struct.unpack("<ffffffffffffH", f.read(50))
            mesh.append([data[3], data[4], data[5]])
            mesh.append([data[6], data[7], data[8]])
            mesh.append([data[9], data[10], data[11]])
        return mesh

    def load3mf(f):
        '''load parts of the 3mf with their properties'''
        namespace = {
            "3mf": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02",
            "m" : "http://schemas.microsoft.com/3dmanufacturing/material/2015/02"
        }
        # The base object of 3mf is a zipped archive.
        archive = zipfile.ZipFile(f, "r")
        try:
            root = ET.parse(archive.open("3D/3dmodel.model"))

            # There can be multiple objects, try to load all of them.
            objects = root.findall("./3mf:resources/3mf:object", namespace)
            if len(objects) == 0:
                print("No objects found in 3MF file %s, either the file is corrupt or you are using an outdated format", f)
                return None
            
            obj_meshs = list()
            c=0
            for obj in objects:
                vertex_list = []
                obj_meshs.append([[],dict()])
                #for vertex in object.mesh.vertices.vertex:
                for vertex in obj.findall(".//3mf:vertex", namespace):
                    vertex_list.append([vertex.get("x"), vertex.get("y"), vertex.get("z")])
                    
                triangles = obj.findall(".//3mf:triangle", namespace)
                #for triangle in object.mesh.triangles.triangle:
                for triangle in triangles:
                    v1 = int(triangle.get("v1"))
                    v2 = int(triangle.get("v2"))
                    v3 = int(triangle.get("v3"))
                    obj_meshs[c][0].append([float(vertex_list[v1][0]),float(vertex_list[v1][1]),float(vertex_list[v1][2])])
                    obj_meshs[c][0].append([float(vertex_list[v2][0]),float(vertex_list[v2][1]),float(vertex_list[v2][2])])
                    obj_meshs[c][0].append([float(vertex_list[v3][0]),float(vertex_list[v3][1]),float(vertex_list[v3][2])])

                transformation = root.findall("./3mf:build/3mf:item[@objectid='{0}']".format(obj.get("id")), namespace)
                if transformation:
                    transformation = transformation[0]
                try:
                    if transformation.get("transform"):
                        splitted_transformation = transformation.get("transform").split()
                        R = [[float(splitted_transformation[0]), float(splitted_transformation[1]), float(splitted_transformation[2])],
                            [float(splitted_transformation[3]), float(splitted_transformation[4]), float(splitted_transformation[5])],
                            [float(splitted_transformation[6]), float(splitted_transformation[7]), float(splitted_transformation[8])]]
                        obj_meshs[c][1]["Rotation"] = R
                        
                except AttributeError:
                    pass # Empty list was found. Getting transformation is not possible

                try:
                    color_list = list()
                    colors = root.findall('.//m:color', namespace)
                    if colors:
                        for color in colors:
                            color_list.append(color.get("color",0))
                        obj_meshs[c][1]["color"] = color_list
                except AttributeError:
                    pass # Empty list was found. Getting transformation is not possible
   
                c=c+1
##            #If there is more then one object, group them.
##            try:
##                if len(objects) > 1:
##                    group_decorator = GroupDecorator()
##                    result.addDecorator(group_decorator)
##            except:
##                pass
                
        except Exception as e:
            print("exception occured in 3mf reader: %s" % e)
            return None
        #print(obj_meshs[0][0])
        return obj_meshs


    def rotateSTL(R, content, filename):
        '''Rotate the object and save as ascii STL'''
        face=[]
        mesh=[]
        i=0

        rotated_content=list(map(FileHandler.rotate_vert, content, [R]*len(content)))
        
        for li in rotated_content:      
            face.append(li)
            i+=1
            if i%3==0:
                mesh.append([face[0],face[1],face[2]])
                face=[]

        mesh = map(FileHandler.calc_nomal, mesh)

        tweaked = list("solid %s" % filename)
        tweaked += list(map(FileHandler.write_facett, mesh))
        tweaked.append("\nendsolid %s\n" % filename)
        tweaked = "".join(tweaked)
        
        return tweaked

    def rotate_vert(a,R):
        return [a[0]*R[0][0]+a[1]*R[1][0]+a[2]*R[2][0],
                              a[0]*R[0][1]+a[1]*R[1][1]+a[2]*R[2][1],
                              a[0]*R[0][2]+a[1]*R[1][2]+a[2]*R[2][2]]
    def calc_nomal(face):
        v=[face[1][0]-face[0][0],face[1][1]-face[0][1],face[1][2]-face[0][2]]
        w=[face[2][0]-face[0][0],face[2][1]-face[0][1],face[2][2]-face[0][2]]
        a=[v[1]*w[2]-v[2]*w[1],v[2]*w[0]-v[0]*w[2],v[0]*w[1]-v[1]*w[0]]        
        return [[a[0],a[1],a[2]],face[0],face[1],face[2]]
    
    def write_facett(facett):
        return"""\nfacet normal %f %f %f
    outer loop
        vertex %f %f %f
        vertex %f %f %f
        vertex %f %f %f
    endloop
endfacet""" % (facett[0][0], facett[0][1], facett[0][2], facett[1][0], 
               facett[1][1], facett[1][2], facett[2][0], facett[2][1], 
                facett[2][2], facett[3][0], facett[3][1], facett[3][2])
        
