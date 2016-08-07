#!/usr/bin/env python3.4
# Author: Christoph Schranz, Salzburg Research

import sys
import math
import random
import time

class Tweak:
    """ The Tweaker is an auto rotate class for 3D objects.
    It requires following mesh format as input:
     [[v1x,v1y,v1z],
      [v2x,v2y,v2z],
      .....
      [vnx,vny,vnz]]
    You can adjust this format in arrange_mesh(). For some applications,
     it is necessary to replace "face[0], face[1]" by "-face[0], -face[1]".

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
    And the relative unprintability of the tweaked object. If this value is
     greater than 15, a support structure is suggested.
        """
    def __init__(self, mesh, bi_algorithmic, verbose, CA=45):
        
        self.bi_algorithmic = bi_algorithmic
        self.workflow(mesh, bi_algorithmic, verbose, CA)
        
    def workflow(self, mesh, bi_algorithmic, verbose, CA):
        n=[0,0,-1]              # default normal vector
        
        content=self.arrange_mesh(mesh)
        
        ## Calculating initial printability
        amin=self.approachfirstvertex(content)
        lit=self.lithograph(content,[0,0,1],amin,CA)
        liste=[[[0,0,1],lit[0], lit[1]]]
        ## vector: , groundA: , OverhangA: %s", liste[0]

        if self.target_function(liste[0][1], liste[0][2]) < 1:
            ## The default orientation is alright!
            bestside=liste[0]
            Unprintability=1.0
        else:
            ## The default orientation is not perfect.
            ## Searching promising orientations: 
            ## Format: [[vector1, gesamtA1],...[vector5, gesamtA5]]: %s", o)
            arcum_time = time.time()
            o=self.area_cumulation(content, n)
            arcum_time = time.time() - arcum_time
            
            if bi_algorithmic:
                dialg_time = time.time()
                o += self.egde_plus_vertex(mesh, 6)
                dialg_time = time.time() - dialg_time          
                
            if verbose:
                print("Examine {} orientations:".format(len(o)))
                for orient in o:
                    print("  "+str(orient[0]))
                
            # Calculate the printability of each orientation
            lit_time = time.time()
            for side in o:
                sn = [float("{:6f}".format(-i)) for i in side[0]]
                ## vector: sn, cum_A: side[1]
                amin=self.approachvertex(content, side[0])
                ret=self.lithograph(content, sn, amin, CA)
                liste.append([sn, ret[0], ret[1]])   #[Vector, touching area, Overhang]
           
            ## Calculating best option
            Unprintability=sys.maxsize
            for i in liste:
                # target function
                F = self.target_function(i[1], i[2]) # touching area: i[1], overhang: i[2]
                if F<Unprintability- 0.2:
                    Unprintability=F
                    bestside=i
                if Unprintability<1: Unprintability=1
                    
            lit_time = time.time() - lit_time
        
        print("""
Time-stats of algorithm:
  Area Cumulation:  \t{ac:6f} s
  Edge plus Vertex:  \t{da:6f} s
  Lithography Time:  \t{lt:6f} s  
  Total Time:        \t{tot:6f} s
""".format(ac=arcum_time, da=dialg_time, lt=lit_time, 
           tot=arcum_time + dialg_time + lit_time))  
           
           
        if bestside:
            [v,phi,R] = self.euler(bestside)
            
        self.v=v
        self.phi=phi
        self.R=R
        self.Unprintability = Unprintability
        self.Zn=bestside[0]
        return None

    def target_function(self, touching, overhang):
        '''This function returns the printability with the touching area and overhang given.'''
        ABSLIMIT=80             # Some values for scaling the printability
        RELLIMIT=1
        F = (overhang/ABSLIMIT) + (overhang/touching/RELLIMIT)
        
        ret = float("{:f}".format(F))
        return ret
        
        
    def arrange_mesh(self, mesh):
        '''The Tweaker needs the mesh format of the object with the normals of the facetts.'''
        face=[]
        content=[]
        i=0
        for li in mesh:      
            face.append(li)
            i+=1
            if i%3==0:
                content.append([])
                v=[face[1][0]-face[0][0],face[1][1]-face[0][1],face[1][2]-face[0][2]]
                w=[face[2][0]-face[0][0],face[2][1]-face[0][1],face[2][2]-face[0][2]]
                a=[v[1]*w[2]-v[2]*w[1],v[2]*w[0]-v[0]*w[2],v[0]*w[1]-v[1]*w[0]]
                content[int(i/3-1)]=[[round(i,6) for i in [a[0],a[1],a[2]]],face[0],face[1],face[2]]
                face=[]
        return content

    
    def approachfirstvertex(self,content):
        '''Returning the lowest z value'''
        amin=sys.maxsize
        for li in content:
            z=min([li[1][2],li[2][2],li[3][2]])
            if z<amin:
                amin=z
        return amin


    def approachvertex(self,content, n):
        '''Returning the lowest value regarding vector n'''
        amin=sys.maxsize
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


    def lithograph(self, content, n, amin, CA):
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

    def egde_plus_vertex(self, mesh, best_n):
        '''Searching normals or random edges with one vertice'''
        orient = dict()
        vcount = len(mesh)
        if vcount < 40000: small = True
        else: small = False
        for i in range(vcount):
            if i%3 == 0:
                v = mesh[i]
                w = mesh[i+1]
        # Skip these cases if file is big due to performance issues.
            elif small:
                if i%3 == 1:
                    v = mesh[i]
                    w = mesh[i+1]
                else:
                    v = mesh[i]
                    w = mesh[i-2]
            else:
                continue
            
            for c in range(5):   
                r_v = random.choice(mesh)
                v = [v[0]-r_v[0], v[1]-r_v[1], v[2]-r_v[2]]
                w = [w[0]-r_v[0], w[1]-r_v[1], w[2]-r_v[2]]
                a=[v[1]*w[2]-v[2]*w[1],v[2]*w[0]-v[0]*w[2],v[0]*w[1]-v[1]*w[0]]
                n = math.sqrt(a[0]*a[0] + a[1]*a[1] + a[2]*a[2])
                if n!=0:
                    a="{:f} {:f} {:f}".format(a[0]/n, a[1]/n, a[2]/n)
                    orient[a] = orient.get(a, 0) + 1
        
        nor = list()
        for k,v in orient.items():
            nor.append((v,k))
            
        nor.sort(reverse=True)
        ret = list()
        for k,v in nor[:best_n]:
            a=[float(i) for i in v.split()]
            ret.append([[a[0],a[1],a[2]],k])
        return ret


    def area_cumulation(self, content, n):
        '''Searching best options out of the objects area vector field'''
        if self.bi_algorithmic: best_n = 6
        else: best_n = 5
        
        orient = list()
        for li in content:       # Cumulate areavectors
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
                           
        # Using n biggest area vectors, if enough orientations were found.
        r=( [0]*best_n )[:len(orient)]
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
                    o.append([i[0], float("{:6f}".format(i[1]))])
                    break
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
            phi = float("{:f}".format(math.pi - math.acos( -bestside[0][2] )))
            v = [-bestside[0][1] , bestside[0][0], 0]
            v = [i / math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2]) for i in v]
            v = [float("{:f}".format(i)) for i in v]

        R = [[v[0] * v[0] * (1 - math.cos(phi)) + math.cos(phi),
              v[0] * v[1] * (1 - math.cos(phi)) - v[2] * math.sin(phi),
              v[0] * v[2] * (1 - math.cos(phi)) + v[1] * math.sin(phi)],
             [v[1] * v[0] * (1 - math.cos(phi)) + v[2] * math.sin(phi),
              v[1] * v[1] * (1 - math.cos(phi)) + math.cos(phi),
              v[1] * v[2] * (1 - math.cos(phi)) - v[0] * math.sin(phi)],
             [v[2] * v[0] * (1 - math.cos(phi)) - v[1] * math.sin(phi),
              v[2] * v[1] * (1 - math.cos(phi)) + v[0] * math.sin(phi),
              v[2] * v[2] * (1 - math.cos(phi)) + math.cos(phi)]]

        R = [[float("{:6f}".format(val)) for val in row] for row in R] 
        
        return [v,phi,R]
