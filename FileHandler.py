#!/usr/bin/env python3.4
# Author: Christoph Schranz, Salzburg Research

import sys, os
import struct
import time
import xml.etree.ElementTree as ET
import ThreeMF


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
                objs = [{"Mesh": FileHandler.loadAsciiSTL(f)}]
                if len(mesh) < 3:
                     f.seek(5, os.SEEK_SET)
                     objs = [{"Mesh": FileHandler.loadBinarySTL(f)}]
            else:
                objs = [{"Mesh": FileHandler.loadBinarySTL(f)}]
                
        elif filetype == ".3mf":
            
            objs = ThreeMF.Read3mf(inputfile)
        else:
            print("File type is not supported.")
            sys.exit()
            
        return objs


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


    def rotate3MF(*arg):
        ThreeMF.rotate3MF(*arg)
        
                  
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
        
