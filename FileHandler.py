#!/usr/bin/env python3.4
# Author: Christoph Schranz, Salzburg Research Forschungsgesellschaft mbH
# Date: 12.01.2016
# STL-tweaker version: 1.13

## Modules required:
## Linux: apt-get install python-pip || Windows: https://pip.pypa.io/en/latest/installing/
## Linux: pip install numpy          || Windows: pip install -i https://pypi.binstar.org/carlkl/simple numpy
## pip install python-utils
## pip install python-utils --upgrade
## pip install numpy-stl
## More infos and licences for this package at https://github.com/WoLpH/numpy-stl

## Usage: <FileHandler.py> <yourobject> [optional: <int(yourownangle)>]

import sys
import os
import platform
import numpy
import time
import logging
logger = logging.getLogger()
import Tweaker


class FileHandler:
    def STLReader(original):
        # Reading mesh data from raw ascii STL content"
        content=[]
        for li in original.split("vertex ")[1:]:
            li=li.split("\n")[0].split(" ")
            x=float(li[0])
            y=float(li[1])
            z=float(li[2])
            content.append([x,y,z])
        #print("\n\nContent:\n"+str(content))
        return content


    def rotate(R, content, name):
        face=[]
        mesh=[]
        i=0
        for li in content:      
            face.append(li)
            i+=1
            if i%3==0:
                mesh.append([])
                a=numpy.cross(numpy.subtract(face[1],face[0]),numpy.subtract(face[2],face[0]))
                mesh[int(i/3-1)]=[[round(i,6) for i in [a[0],a[1],a[2]]],face[0],face[1],face[2]]
                face=[]
        content=mesh
            
        logger.debug("create resulting ascii stl using solid name %s", name)
        tweaked = "solid %s" % name
        for li in content:
            for vert in range(len(li)-1):
                li[vert + 1] = (li[vert + 1] * R).getA1()  # rotational matrix with array transformation
            n = numpy.cross(numpy.subtract(li[1], li[2]), numpy.subtract(li[1], li[3]))
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
    stime=time.time()
    le=len(sys.argv) 
    stlfile=str(sys.argv[1])
    size=os.stat(stlfile).st_size
    fileSizeLimit=2000000   # if the file is bigger '(in bytes), tweaking would take some moments
    if size<fileSizeLimit:
        further='yes'
    else:
        print("The size of your object in bytes: %s" %size)
        print("Your file is very huge. A tweak would last a while!")
        further=raw_input("but surely you can do it! (yes/no) ")
    if (further=='yes') & (le in [2,3]):
        print("Finding the best orientation for your object")
        f=sys.argv[1]
        
        if f.split(".")[-1].lower() == "stl":
            name=f.split("/")[-1].split(".")[0]        
            logger.debug("...calculating the printability of a new object")        
            ascii=f.split(".")[0]+"_ascii."+f.split(".")[1]
            logger.debug("...generating ascii file")
            os.system("stl2ascii %s %s" %(f,ascii)) # In case of troubles check the module infos at the top or https://github.com/WoLpH/numpy-stl if troubled       
            original=open(ascii,"r").read()
            os.system("%s %s" %({'Windows':'del','Linux':'rm'}.get(platform.system()),ascii))

            logger.debug("...arranging original content")
            content=FileHandler.STLReader(original)
            
            if le==3:
                CA=int(sys.argv[2])
                try:
                    x=Tweaker.Tweak(content, CA) #[v,phi,R,F]
                except (KeyboardInterrupt, SystemExit):
                    raise
            elif le==2:
                try:
                    x=Tweaker.Tweak(content)          
                except (KeyboardInterrupt, SystemExit):
                    raise

            print("\n\nv: "+str(x.v))
            print("\n\nphi: "+str(x.phi))
            print("\n\nR: "+str(x.R))
            print("\n\nUnprintability: "+str(x.Unprintability)+"\n\n\n")
            
            tweakedcontent=FileHandler.rotate(x.R, content, name)
            if x.Unprintability > 12:
                logger.debug("Your object is tricky to print. Use a support structure!")
                tweakedcontent+=" {supportstructure:yes}"
            logger.debug("Rotated")
            
            tweaked=f.split(".")[0]+"_tweaked."+f.split(".")[1]
            with open(tweaked,'w') as outfile:
                outfile.write(tweakedcontent)
                
            endtime=time.time()
            print("Tweaking took {} s.".format(endtime-stime))
            print("\n\nSuccessfully Rotated!")
           
    else:
        logger.warning("You have to load a STL file.")
        print("""Your command should be of the form <FileHandler.py> 
        <yourobject> [optional: <int(yourownangle)>]""")
