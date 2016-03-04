#!/usr/bin/env python3.4
# Author: Christoph Schranz, Salzburg Research
# Date: 3.3.2016
# STL-tweaker version: 4.3.16

## Modules required:
##  Linux:  apt-get install python-pip
##  Linux:  pip install numpy
##  Windows: https://pip.pypa.io/en/latest/installing/
##  Windows: pip install -i https://pypi.binstar.org/carlkl/simple numpy

## Usage:
##  Call the function Tweaker.Tweak(mesh_content).
##  Note the correct mesh format, which can be configured in arrange_mesh
##  Call the methods v, phi, R, Zn or Unprintability. View the doc for more informations

import math
import numpy
import logging
import time
logger = logging.getLogger()

class Tweak:
    """ The Tweaker is an auto rotate class for 3D objects.
    It requires following mesh format as input:
     [[v1x,v1y,v1z],
      [v2x,v2y,v2z],
      .....
      [vnx,vny,vnz]]
    If you want to use the mesh format with inversed x and y coords, go to
    arrange_mesh() and replace "face[0], face[1]" by "-face[0], -face[1]".
    Also note the orientation of the z-axis.

    The critical angle CA is a variable that can be set by the operator as
    it may depend on multiple factors such as material used, printing
    temperature, printing speed, etc.

    Following attributes of the class are supported:
    The tweaked z-axis' vector .z.
    Euler coords .v and .phi, where v is orthogonal to both z and z' and phi
    the angle between z and z' in rad.
    The rotational matrix .R, the new mesh is created, by multiplying each
    vector with R.
    The vector of the new
    And the relative .Unprintability of the tweaked object. If this value is
    greater than 15, a support structure is suggested."""
    
    def __init__(self, content, CA=40):
        self.content=content
        self.CA=CA
        self.workflow(self.content, self.CA)

    def workflow(self,content, CA):
        ABSLIMIT=80             # Some values to scale the printability
        RELLIMIT=1
        n=[0,0,-1]              # default z vector

        content=self.arrange_mesh(content)      
        logger.debug("CA=%i\n...calculating initial lithographs", CA)
        [content_an, amin] = self.approachfirstvertex(content)
        lit=self.lithograph(content_an, [0,0,1], amin, CA)
        liste=[[[0,0,1],lit[0], lit[1]]]
        logger.info("vector: , groundA: , OverhangA: %s", liste[0])
        
        if (liste[0][2]/ABSLIMIT)+(liste[0][2]/liste[0][1]/RELLIMIT)<1:
            logger.debug("The default orientation is alright!")
            bestside=liste[0]
            Unprintability=1
        else:
            logger.debug("The default orientation is not perfect.")
            logger.debug("...calculating orientations")
            o=self.orientation(content, n)
            logger.info("Orient: [[vector1, gesamtA1],...[vector5, gesamtA5]]:%s", o)
            for side in o:
                sn=[round(-i,6)+0 for i in side[0]]
                logger.info("side: [vector: %s, gesamtA: %s]",sn, side[1])
                [content_an, amin] = self.approachvertex(content, side[0])
                logger.info("amin:", amin)
                ret=self.lithograph(content_an, sn, amin, CA)
                logger.info("Ground, Overhang: %s",ret)
                liste.append([sn, ret[0], ret[1]])   #[Vector, touching area, Overhang]
            logger.debug("...calculating best option")
            Unprintability=999999999
            for i in liste:
                F=(i[2]/ABSLIMIT)+(i[2]/i[1]/RELLIMIT)  # target function, make it extern
                logger.info("Side: %s / Unprintability %s",i,F)
                if F<Unprintability-0.2:
                    Unprintability=F
                    bestside=i
                if Unprintability<1:
                    Unprintability=1          
        logger.info("best side %s with Unprintability: %f", bestside, Unprintability)
        #print("best side %s with Unprintability: %f"% (bestside, Unprintability))
        if bestside:
            [v,phi,R] = self.euler(bestside)
            logger.debug("Finished!") 
        self.v=v
        self.phi=phi
        self.R=R
        self.Unprintability=Unprintability
        self.Zn=bestside
        return None

    def arrange_mesh(self,content):
        '''The Tweaker needs the content of the mesh object with the normals of the facetts.'''
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
        return mesh
  
    def approachfirstvertex(self,content):
        '''Returning the lowest z value'''
        amin=999999999
        for li in content:
            z=min([li[1][2],li[2][2],li[3][2]])
            li.append(z)
            if z<amin:
                amin=z
        return [content, amin]

    def approachvertex(self,content, n):
        '''Returning the lowest value regarding vector n'''
        amin=999999999
        n=[-i for i in n]
        l=len(content[0])==3
        norm=numpy.linalg.norm(n)
        for li in content:
            a1=numpy.inner(li[1],n)/norm
            a2=numpy.inner(li[2],n)/norm
            a3=numpy.inner(li[3],n)/norm              
            an=min([a1,a2,a3])
            li[4]=an
            if an<amin:
                amin=an
        return [content, amin]

    def lithograph(self,content,n,amin, CA):
        '''Calculating touching areas and overhangs regarding the vector n'''
        Overhang=1
        alpha=-math.cos((90-CA)*math.pi/180)
        Grundfl=1
        for li in content:
            a=numpy.array(li[0])
            norma=numpy.linalg.norm(a)
            if norma>2:      
                if alpha > numpy.inner(a,n)/(norma):
                    an=li[4]
                    ali=round(abs(numpy.inner(li[0],n))/2,6)
                    if an>amin+0.3:
                        Overhang+=ali
                    else:
                        Grundfl+=ali
        #print("\n\n[Grundfl, Overhang]:\n"+str([Grundfl, Overhang]))
        return [Grundfl, Overhang]

    def orientation(self,content,n):
        '''Searching best orientations in the objects area vector field'''
        orient=[]
        for li in content:
            an=li[0]
            norma=round(numpy.linalg.norm(an),8)
            
            if norma!=0:
                an=[round(i/norma+0, 5) for i in an]
                if an!=n: 
                    A=round(numpy.linalg.norm(numpy.cross(numpy.subtract(li[1],li[2]),
                                                          numpy.subtract(li[3],li[2])))/2, 4)
                    if A>0.5: # Smaller areas don't worry 
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
        #print("\nOrientation: \n" +str(o))
        return o

    def euler(self, bestside):
        '''Calculating euler params and rotational matrix'''
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
        return [v,phi,R]
