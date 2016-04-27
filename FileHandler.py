#!/usr/bin/env python3.4
# Author: Christoph Schranz, Salzburg Research Forschungsgesellschaft mbH
# Date: 12.01.2016
# STL-tweaker version: 0603

## Modules required (only for binary STLs)
## Linux: apt-get install python-pip
## Linux: pip install numpy
## Windows: https://pip.pypa.io/en/latest/installing/
## Windows: pip install -i https://pypi.binstar.org/carlkl/simple numpy
## pip install python-utils
## pip install python-utils --upgrade
## pip install numpy-stl
## More infos and licences for this package at https://github.com/WoLpH/numpy-stl

## Usage: <FileHandler.py> <yourobject.stl> [optional: <int(yourownangle)>]

import sys
import os
import platform
import logging
logger = logging.getLogger()
import Tweaker


class FileHandler:
    '''Open STL file and return content as ascii.'''
    def openSTL(f):
        try:
            ofile=open(f,"r")
            original=ofile.read()
            if len(original) == os.path.getsize(f) > 0:
                readsucceed=True
                print("Reading ascii STL")
                logger.debug("The file is a proper ascii STL.")
            else:
                readsucceed=False
                logger.debug("The file is not a proper ascii STL.")
        except:
            logger.debug("The file is not an ascii STL.")
            readsucceed=False
        if not readsucceed:
            try:
                fascii=f.split(".")[0]+"_ascii."+f.split(".")[1]
                logger.debug("...generating ascii file")
                # In case of troubles check the module infos at the top or
                # https://github.com/WoLpH/numpy-stl
                os.system("stl2ascii %s %s" %(f,fascii))
                original=open(fascii,"r").read()

                if len(original) == os.path.getsize(fascii) > 0:
                    readsucceed=True
                    print("Reading STL file")
                else:
                    logger.debug("Else: stl2ascii function of numpy-stl seems not to work")
                os.system("%s %s" %({'Windows':'del','Linux':'rm'}.get(platform.system()),fascii))
            except:
                logger.debug("Try-exception: stl2ascii function of numpy-stl seems not to work")
        if not readsucceed:
            print("File couldn't be read")
            print("""Check the stl2ascii function of numpy-stl: https://github.com/WoLpH/numpy-stl""")
                    
        return (original, readsucceed)
        
    def STLReader(original):
        '''Read mesh data from ascii content'''
        content=[]
        for li in original.split("vertex ")[1:]:
            li=li.split("\n")[0].split(" ")
            x=float(li[0])
            y=float(li[1])
            z=float(li[2])
            content.append([x,y,z])
        return content


    def rotate(R, content, name):
        '''Rotate the object and save as ascii STL'''
        face=[]
        mesh=[]
        i=0
        for li in content:      
            face.append(li)
            i+=1
            if i%3==0:
                mesh.append([])
                v=[face[1][0]-face[0][0],face[1][1]-face[0][1],face[1][2]-face[0][2]]
                w=[face[2][0]-face[0][0],face[2][1]-face[0][1],face[2][2]-face[0][2]]
                a=[v[1]*w[2]-v[2]*w[1],v[2]*w[0]-v[0]*w[2],v[0]*w[1]-v[1]*w[0]]
                mesh[int(i/3-1)]=[[round(i,6) for i in [a[0],a[1],a[2]]],face[0],face[1],face[2]]
                face=[]
        content=mesh
            
        logger.debug("create resulting ascii stl using solid name %s", name)
        tweaked = "solid %s" % name
        for li in content:
            for vert in range(len(li)-1):
                a=li[vert + 1]
                # multiply vectors with rotational matrix R
                li[vert + 1]=[a[0]*R[0][0]+a[1]*R[1][0]+a[2]*R[2][0],
                              a[0]*R[0][1]+a[1]*R[1][1]+a[2]*R[2][1],
                              a[0]*R[0][2]+a[1]*R[1][2]+a[2]*R[2][2]]
            v=[li[1][0]-li[2][0], li[1][1]-li[2][1], li[1][2]-li[2][2]]
            w=[li[1][0]-li[3][0], li[1][1]-li[3][1], li[1][2]-li[3][2]]
            n=[v[1]*w[2]-v[2]*w[1],v[2]*w[0]-v[0]*w[2],v[0]*w[1]-v[1]*w[0]]

            tweaked += """\nfacet normal %f %f %f
    outer loop
    vertex %f %f %f
    vertex %f %f %f
    vertex %f %f %f
    endloop
    endfacet""" % (n[0], n[1], n[2], li[1][0], li[1][1], li[1][2], li[2][0], li[2][1], li[2][2], li[3][0], li[3][1],
               li[3][2])
    
        tweaked += "\nendsolid %s\n" % name

        return tweaked


if __name__ == "__main__":
    if len(sys.argv) in [2,3]:
        logger.debug("...finding best orientation.")
        f=sys.argv[1]
        
        if f.split(".")[-1].lower() == "stl":
            name=f.split("/")[-1].split(".")[0]
            logger.debug("...opening new object")
            (original, readsucceed) = FileHandler.openSTL(f)

            if readsucceed:
                logger.debug("...arranging original content")
                content = FileHandler.STLReader(original)
                          
                if len(sys.argv)==3:
                    CA=int(sys.argv[2])
                    try:
                        x=Tweaker.Tweak(content, CA)
                    except (KeyboardInterrupt, SystemExit):
                        raise
                else:
                    try:
                        x=Tweaker.Tweak(content)          
                    except (KeyboardInterrupt, SystemExit):
                        raise
                #Variables: v, phi, R, F, Unprintability
                #print("\nv: "+str(x.v))
                #print("phi: "+str(x.phi))
                #print("Tweaked Z-axis: "+str(x.Zn))
                #print("R: "+str(x.R))
                #print("Unprintability: "+str(x.Unprintability))

                if x.Zn==[0,0,1]:
                    tweakedcontent=original
                else:
                    tweakedcontent=FileHandler.rotate(x.R, content, name)
                    
                if x.Unprintability > 7:
                    logger.debug("Your object is tricky to print. Use a support structure!")
                    tweakedcontent+=" {supportstructure:yes}"
                logger.debug("Rotated")
                
                tweaked=f.split(".")[0]+"_tweaked."+f.split(".")[-1]
                with open(tweaked,'w') as outfile:
                    outfile.write(tweakedcontent)
                print("\nSuccessfully Rotated!")
        else:
            print("You have to use a stl file")
            logger.warning("You have to load a STL Object.")
    else:
        logger.warning("You have to load a STL file.")
        print("""Your command should be of the form <FileHandler.py> 
        <yourobject> [optional: <int(yourownangle)>]""")
