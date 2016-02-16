#!/usr/bin/env python
# Author: Christoph Schranz, Salzburg Research Forschungsgesellschaft mbH
# Date: 12.01.2016
# Python version: 2.7
# STL-tweaker version: 1.13

# Modules required:
# Linux: apt-get install python-pip || Windows: https://pip.pypa.io/en/latest/installing/
# Linux: pip install numpy          || Windows: pip install -i https://pypi.binstar.org/carlkl/simple numpy
# pip install python-utils
# pip install python-utils --upgrade
# pip install numpy-stl
# More infos and licences for this package at https://github.com/WoLpH/numpy-stl

# Usage: <stl_tweaker_versionx.py> <yourobject.stl> [optional: <int(yourownangle)>]

import sys
import os
import platform
import math
import numpy
import logging
logger = logging.getLogger()

fileSizeLimit=2000000   # if the file is bigger '(in bytes), tweaking would take some moments
ABSLIMIT=80             # Some values to scale the printability
RELLIMIT=1
n=[0,0,-1]              # normal vektor

def tweak(f,CA=45):  # you just need the filepath f
    if f.split(".")[-1].lower() == "stl":
        name=f.split("/")[-1].split(".")[0]
        
        logger.debug("...calculating the printability of a new object")        
        ascii=f.split(".")[0]+"_ascii."+f.split(".")[1]
        logger.debug("...generating ascii file")
        os.system("stl2ascii %s %s" %(f,ascii)) # In case of troubles check the module infos at the top or https://github.com/WoLpH/numpy-stl if troubled       
        original=open(ascii,"r").read()
        system=platform.system()
        if system=='Windows':
            remove='del'
            copy='copy'
        else:
            remove='rm'
            copy='cp'
        os.system("%s %s" %(remove,ascii))

        logger.debug("...arranging original content")
        content=arrange(original)
        
        logger.debug("CA=%i\n...calculating initial lithographs", CA)
        amin=approachfirstvertex(content)
        lit=lithograph(content,[0,0,1],amin,CA)
        liste=[[[0,0,1],lit[0], lit[1]]]
        logger.info("vector: , groundA: , OverhangA: %s", liste[0])

        if (liste[0][2]/ABSLIMIT)+(liste[0][2]/liste[0][1]/RELLIMIT)<1:
            logger.debug("The default orientation is alright!")
            bestside=liste[0]
            rotated = rotate(bestside,content, name)
            Fmin=1
            print "The default orientation is alright!"
        else:
            logger.debug("The default orientation is not perfect.")
            logger.debug("...calculating orientations")
            o=orientation(content)
            logger.info("Orient: [[vector1, gesamtA1],...[vector5, gesamtA5]]: %s", o)
            
            for side in o:
                sn=[round(-i,6)+0 for i in side[0]]                
                logger.info("side: [vector: %s, gesamtA: %s]",sn, side[1])
                amin=approachvertex(content, side[0])
                logger.info("amin:", amin)
                ret=lithograph(content,sn,amin,CA)
                logger.info("Ground, Overhang: %s",ret)
                liste.append([sn, ret[0], ret[1]])   #[Vektor, ground, Overhang]
            
            logger.debug("...calculating best option")
            Fmin=99999
            for i in liste:
                F=(i[2]/ABSLIMIT)+(i[2]/i[1]/RELLIMIT)  # target function
                logger.info("Side: %s / printability %s",i,F)
                if F<Fmin:
                    Fmin=F
                    bestside=i

        logger.info("best side %s with F: %f", bestside, Fmin)
        #print("The file has a relative unprintability of %f"%Fmin)
        
        if bestside:
##                if bestside[0] == [0, 0, 1]:
##                    rotated = original
##                else:
##                    rotated = rotate(bestside,content, name)
            rotated = rotate(bestside,content, name)
            if Fmin > 12:
                logger.debug("Your object is quite tricky to print. Use a support structure!")
                rotated+=" {supportstructure:yes}"
            logger.debug("Rotated")
            
            tweaked=f.split(".")[0]+"_tweaked."+f.split(".")[1]
            with open(tweaked,'w') as outfile:
                outfile.write(rotated)
            logger.debug("Finished!")
            print "Finished!"
        else:
            logger.warning("No optimal orientation found")
    else:
        logger.warning("You have to load a STL file.")


def arrange(content): # Calculate Overhang
    litho=content.split("facet ")
    ret=[]
    for li in range(content.count("facet ")):       #Calculate areavectors
        ret.append([])
        normal=litho[li+1].split("normal ")[1].split("\n")[0]
        xn=float(normal.split(" ")[0])
        yn=float(normal.split(" ")[1])
        zn=float(normal.split(" ")[2])
        
        vertex=litho[li+1].split("outer loop")[1].split("endloop")[0].split("vertex")              
        x1=float(vertex[1].split(" ")[1])
        y1=float(vertex[1].split(" ")[2])
        z1=float(vertex[1].split(" ")[3])
        x2=float(vertex[2].split(" ")[1])
        y2=float(vertex[2].split(" ")[2])
        z2=float(vertex[2].split(" ")[3])
        x3=float(vertex[3].split(" ")[1])
        y3=float(vertex[3].split(" ")[2])
        z3=float(vertex[3].split(" ")[3])
                
        ret[li]=[[xn,yn,zn],[x1,y1,z1],[x2,y2,z2],[x3,y3,z3]]
      
    return ret


def approachfirstvertex(content):
    amin=999999
    for li in content:        
        z1=li[1][2]
        z2=li[2][2]
        z3=li[3][2]
        z=min([z1,z2,z3])
        if z<amin:
            amin=z   
    return amin


def approachvertex(content, n):
    amin=99999        # Searching initial layer
    n=[-i for i in n]
    for li in content:                     
        [x1,y1,z1],[x2,y2,z2],[x3,y3,z3]=li[1:]
        a1=numpy.inner([x1,y1,z1],n)/numpy.linalg.norm(n)
        a2=numpy.inner([x2,y2,z2],n)/numpy.linalg.norm(n)
        a3=numpy.inner([x3,y3,z3],n)/numpy.linalg.norm(n)              
        an=min([a1,a2,a3])
        if an<amin:
            amin=an
    return amin


def lithograph(content,n,amin, CA): # Calculate Overhang
    Overhang=1
    alpha=-math.cos((90-CA)*math.pi/180)
    Grundfl=1
    for li in content:       #Calculate areavectors
        a=numpy.array(li[0])
        norma=numpy.linalg.norm(a)
        
        if norma>2:      
            if alpha > numpy.inner(a,n)/(norma*numpy.linalg.norm(n)):           ######Here      
                [x1,y1,z1],[x2,y2,z2],[x3,y3,z3]=li[1:]              
                # minimal projection of vertex at n
                a1=numpy.inner([x1,y1,z1],n)/numpy.linalg.norm(n)
                a2=numpy.inner([x2,y2,z2],n)/numpy.linalg.norm(n)
                a3=numpy.inner([x3,y3,z3],n)/numpy.linalg.norm(n)
                an=min([a1,a2,a3])
                a1=[x1,y1,z1]
                a2=[x2,y2,z2]
                a3=[x3,y3,z3]
                ali=numpy.cross(numpy.subtract([x1,y1,z1],[x2,y2,z2]),numpy.subtract([x3,y3,z3],[x2,y2,z2]))/2
                ali=round(abs(numpy.inner(ali,n)),6)
                
                if an>amin+0.3:
                    Overhang+=ali
                else:
                    Grundfl+=ali                  
    return [Grundfl, Overhang]


def orientation(content):    # Creating Area-Vector Field Graphs
    orient=[]
    for li in content:       #Calculate areavectors
        an=li[0]
        norma=round(numpy.linalg.norm(an),8)
        
        if norma!=0:
            an=[round(i/norma+0, 5) for i in an]
            if an!=n: 
                [x1,y1,z1],[x2,y2,z2],[x3,y3,z3]=li[1:]
                A=round(numpy.linalg.norm(numpy.cross(numpy.subtract([x1,y1,z1],[x2,y2,z2]),numpy.subtract([x3,y3,z3],[x2,y2,z2])))/2, 4)

                if A>0.5: # Smaller areas doesn't worry 
                    orien=0
                    for i in orient:
                        if i[0]==an:
                            i[1]+=A
                            orien=1
                    if orien==0:
                       orient.append([an,A])                   
    # Use the 6 favored area vectors
    r=[0,0,0,0,0,0][:len(orient)]
    for i in orient:
        if i[1] > min(r):
            r.remove(min(r))
            r.append(i[1])
    o=[]
    for i in range(r.count(0)):
        r=r.remove(0)
    for c in r:
        for i in orient:
            if c==i[1]:
                o.append(i)
                break
    return o


def rotate(bestside, content, name):
    logger.info("trying to rotate ascii stl content, bestside: %s", bestside)
    if bestside[0] == [0, 0, -1]:
        v = [1, 0, 0]
        phi = math.pi
    elif bestside[0]==[0,0,1]:
        v=[1,0,0]
        phi=0
    else:
        phi = math.pi - math.acos(numpy.inner(bestside[0], [0, 0, -1]))
        v = [round(i, 5) + 0 for i in numpy.cross(bestside[0], [0, 0, -1])]
        v = [i / numpy.linalg.norm(v) for i in v]
    logger.info("v: %s", v)
    logger.info("rotating object: phi: %s rad = %s degrees", phi, phi * 180 / math.pi)

    R = numpy.matrix([[v[0] * v[0] * (1 - math.cos(phi)) + math.cos(phi),
                       v[0] * v[1] * (1 - math.cos(phi)) - v[2] * math.sin(phi),
                       v[0] * v[2] * (1 - math.cos(phi)) + v[1] * math.sin(phi)],
                      [v[1] * v[0] * (1 - math.cos(phi)) + v[2] * math.sin(phi),
                       v[1] * v[1] * (1 - math.cos(phi)) + math.cos(phi),
                       v[1] * v[2] * (1 - math.cos(phi)) - v[0] * math.sin(phi)],
                      [v[2] * v[0] * (1 - math.cos(phi)) - v[1] * math.sin(phi),
                       v[2] * v[1] * (1 - math.cos(phi)) + v[0] * math.sin(phi),
                       v[2] * v[2] * (1 - math.cos(phi)) + math.cos(phi)]])

    logger.debug("create resulting ascii stl using solid name %s", name)
    result = "solid %s" % name
    for li in content:
        for vert in range(len(li) - 1):
            li[vert + 1] = (li[vert + 1] * R).getA1()  # rotational matrix with array transformation
        n = numpy.cross(numpy.subtract(li[1], li[2]), numpy.subtract(li[1], li[3]))
        result += """\nfacet normal %f %f %f
outer loop
vertex %f %f %f
vertex %f %f %f
vertex %f %f %f
endloop
endfacet""" % (n[0], n[1], n[2], li[1][0], li[1][1], li[1][2], li[2][0], li[2][1], li[2][2], li[3][0], li[3][1],
           li[3][2])

    result += "\nendsolid %s\n" % name
    return result


if __name__ == "__main__":
    le=len(sys.argv) 
    stlfile=str(sys.argv[1])
    size=os.stat(stlfile).st_size
    if size<fileSizeLimit:
        further='yes'
    else:
        print "The size of your object in bytes: %s" %size
        print "Your file is very huge. A tweak would last a while,"
        further=raw_input("but surely you can do it! (yes/no) ")
    if further=='yes':
        print "Finding the best orientation for your object"
        if le==3:
            CA=int(sys.argv[2])
            try:
                tweak(stlfile, CA)
            except (KeyboardInterrupt, SystemExit):
                raise
        elif le==2:
            try:
                tweak(stlfile)          
            except (KeyboardInterrupt, SystemExit):
                raise
            
        else:
            print """Your command should be of the form <python> <stl_tweaker_versionx.py> 
            <yourobject.stl> [optional: <int(yourownangle)>]"""

