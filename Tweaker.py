#!/usr/bin/env python3.4
# Author: Christoph Schranz, Salzburg Research
# Date: 3.3.2016
# STL-tweaker version: 9.3.16

## Usage:
##  Call the function Tweaker.Tweak(mesh_content).
##  Note the correct mesh format, which can be configured in arrange_mesh
##  Call the methods v,phi,R, Zn or Unprintability. View the doc for more informations

import math
import logging
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
    greater than 15, a support structure is suggested.
        """
    def __init__(self, content, CA=45):
        self.content=content
        self.CA=CA
        self.workflow(self.content, self.CA)

    def workflow(self,content, CA):
        ABSLIMIT=80             # Some values to scale the printability
        RELLIMIT=1
        n=[0,0,-1]              # default normal vector

        content=self.arrange_mesh(content)
        
        logger.debug("CA=%i\n...calculating initial lithographs", CA)
        amin=self.approachfirstvertex(content)
        lit=self.lithograph(content,[0,0,1],amin,CA)
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
            logger.info("Orient: [[vector1, gesamtA1],...[vector5, gesamtA5]]: %s", o)
            
            for side in o:
                sn=[round(-i,6)+0 for i in side[0]]
                logger.info("side: [vector: %s, gesamtA: %s]",sn, side[1])
                amin=self.approachvertex(content, side[0])
                logger.info("amin:", amin)
                ret=self.lithograph(content, sn, amin, CA)
                logger.info("Ground, Overhang: %s",ret)
                liste.append([sn, ret[0], ret[1]])   #[Vector, touching area, Overhang]
            
            logger.debug("...calculating best option")
            Unprintability=999999999
            for i in liste:
                F=(i[2]/ABSLIMIT)+(i[2]/i[1]/RELLIMIT)  # target function
                logger.info("Side: %s / Unprintability %s",i,F)
                if F<Unprintability-0.2:
                    Unprintability=F
                    bestside=i
                if Unprintability<1:
                    Unprintability=1
                    
        logger.info("best side %s with Unprintability: %f", bestside, Unprintability)
        
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
                v=[face[1][0]-face[0][0],face[1][1]-face[0][1],face[1][2]-face[0][2]]
                w=[face[2][0]-face[0][0],face[2][1]-face[0][1],face[2][2]-face[0][2]]
                a=[v[1]*w[2]-v[2]*w[1],v[2]*w[0]-v[0]*w[2],v[0]*w[1]-v[1]*w[0]]
                mesh[int(i/3-1)]=[[round(i,6) for i in [a[0],a[1],a[2]]],face[0],face[1],face[2]]
                face=[]
        return mesh

    
    def approachfirstvertex(self,content):
        '''Returning the lowest z value'''
        amin=999999999
        for li in content:
            z=min([li[1][2],li[2][2],li[3][2]])
            if z<amin:
                amin=z
        return amin


    def approachvertex(self,content, n):
        '''Returning the lowest value regarding vector n'''
        amin=999999999
        n=[-i for i in n]
        normn=math.sqrt(n[0]*n[0] + n[1]*n[1] + n[2]*n[2])
        for li in content:
            a1=(li[1][0]*n[0] +li[1][1]*n[1] +li[1][2]*n[2])/normn
            a2=(li[2][0]*n[0] +li[2][1]*n[1] +li[2][2]*n[2])/normn
            a3=(li[3][0]*n[0] +li[3][1]*n[1] +li[3][2]*n[2])/normn           
            an=min([a1,a2,a3])
            if an<amin:
                amin=an
        return amin


    def lithograph(self,content,n,amin, CA):
        '''Calculating touching areas and overhangs regarding the vector n'''
        Overhang=1
        alpha=-math.cos((90-CA)*math.pi/180)
        Grundfl=1
        for li in content:
            a=li[0]
            norma=math.sqrt(a[0]*a[0] + a[1]*a[1] + a[2]*a[2])
            normn=math.sqrt(n[0]*n[0] + n[1]*n[1] + n[2]*n[2])
            if norma>2:      
                if alpha > (a[0]*n[0] +a[1]*n[1] +a[2]*n[2])/(norma*normn):
                    a1=(li[1][0]*n[0] +li[1][1]*n[1] +li[1][2]*n[2])/normn
                    a2=(li[2][0]*n[0] +li[2][1]*n[1] +li[2][2]*n[2])/normn
                    a3=(li[3][0]*n[0] +li[3][1]*n[1] +li[3][2]*n[2])/normn 
                    an=min([a1,a2,a3])

                    ali=round(abs(li[0][0]*n[0] +li[0][1]*n[1] +li[0][2]*n[2])/2,6)
                    if an>amin+0.3:
                        Overhang+=ali
                    else:
                        Grundfl+=ali
        return [Grundfl, Overhang]


    def orientation(self,content,n):
        '''Searching best options out of the objects area vector field'''
        orient=[]
        for li in content:       #Calculate areavectors
            an=li[0]
            norma=round(math.sqrt(an[0]*an[0] + an[1]*an[1] + an[2]*an[2]),8)
            
            if norma!=0:
                an=[round(i/norma+0, 5) for i in an]
                if an!=n:
                    v=[li[2][0]-li[1][0], li[2][1]-li[1][1], li[2][2]-li[1][2]]
                    w=[li[2][0]-li[3][0], li[2][1]-li[3][1], li[2][2]-li[3][2]]
                    x=[v[1]*w[2]-v[2]*w[1],v[2]*w[0]-v[0]*w[2],v[0]*w[1]-v[1]*w[0]]
                    A=round(math.sqrt(x[0]*x[0] + x[1]*x[1] + x[2]*x[2])/2, 4)
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
            phi = math.pi - math.acos( -bestside[0][2] )
            v = [round(i, 5) + 0 for i in   [-bestside[0][1] , bestside[0][0], 0]]
            v = [i / math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2]) for i in v]
        logger.info("v: %s", v)
        logger.info("rotating object: phi: %s rad = %s degrees", phi, phi * 180 / math.pi)

        R = [[v[0] * v[0] * (1 - math.cos(phi)) + math.cos(phi),
             v[0] * v[1] * (1 - math.cos(phi)) - v[2] * math.sin(phi),
             v[0] * v[2] * (1 - math.cos(phi)) + v[1] * math.sin(phi)],
             [v[1] * v[0] * (1 - math.cos(phi)) + v[2] * math.sin(phi),
              v[1] * v[1] * (1 - math.cos(phi)) + math.cos(phi),
              v[1] * v[2] * (1 - math.cos(phi)) - v[0] * math.sin(phi)],
             [v[2] * v[0] * (1 - math.cos(phi)) - v[1] * math.sin(phi),
              v[2] * v[1] * (1 - math.cos(phi)) + v[0] * math.sin(phi),
              v[2] * v[2] * (1 - math.cos(phi)) + math.cos(phi)]]
        return [v,phi,R]
