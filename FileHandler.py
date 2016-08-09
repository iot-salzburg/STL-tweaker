#!/usr/bin/env python3.4
# Author: Christoph Schranz, Salzburg Research

## You can preset the default model in line 104

import sys, argparse
import os
import struct
import time
from Tweaker import Tweak


class FileHandler:      
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
        #print("binary mesh {} {}".format(faceCount, len(mesh)))
        return mesh

    def rotate(R, content, filename):
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
            
        tweaked = "solid %s" % filename
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
    
        tweaked += "\nendsolid %s\n" % filename

        return tweaked
    
    def getargs():
        parser = argparse.ArgumentParser(description=
                "Orientation tool for better 3D prints")
        parser.add_argument('-vb', '--verbose', action="store_true",dest="verbose", 
                            help="increase output verbosity", default=False)
        parser.add_argument('-i', action="store",  
                            dest="inputfile", help="select input file")
        parser.add_argument('-o', action="store", dest="outputfile",
                            help="select output file. '_tweaked' is postfix by default")
        parser.add_argument('-a', '--angle', action="store", dest="angle", type=int,
                            default=45,
                            help="specify critical angle for overhang demarcation in degrees")
        parser.add_argument('-b', '--bi', action="store_true", dest="bi_algorithmic", default=False,
                            help="using two algorithms for calculation")
        parser.add_argument('-v', '--version', action="store_true", dest="version",
                            help="print version number and exit", default=False)
        parser.add_argument('-r', '--result', action="store_true", dest="result",
                            help="show result of calculation and exit without creating output file",
                            default=False)                            
        args = parser.parse_args()

        if args.version:
            print("Tweaker 0.2.5, (9 August 2016)")
            return None
            
        if not args.inputfile:   
            curpath = os.path.dirname(os.path.realpath(__file__))
            args.inputfile=curpath + os.sep + "demo_object.stl"
            #args.inputfile=curpath + os.sep + "kugel_konisch.stl"

            
    
        if not args.outputfile:
            args.outputfile = os.path.splitext(args.inputfile)[0] + "_tweaked" 
            args.outputfile += os.path.splitext(args.inputfile)[1].lower()
               
        argv = sys.argv[1:]
        if len(argv)==0:
            print("""No additional arguments. Testing calculation with 
demo object in verbose and bi-algorithmic mode. Use argument -h for help.
""")
            args.verbose = True
            args.bi_algorithmic = True
            
        elif os.path.splitext(args.inputfile)[1].lower() != ".stl":
            print("File type is not supported.")
            return None
                
        return args


if __name__ == "__main__":
    ## Get the command line arguments. If no arguments were found
    ## a demo object file will be tweaked.
    stime=time.time()
    try:
        args = FileHandler.getargs()
        if args is None:
            sys.exit()
    except:
        sys.exit()
                        
    ## loading mesh format
    f=open(args.inputfile,"rb")
    if "solid" in str(f.read(5).lower()):
        f=open(args.inputfile,"r")
        mesh=FileHandler.loadAsciiSTL(f)
        if len(mesh) < 3:
             f.seek(5, os.SEEK_SET)
             mesh=FileHandler.loadBinarySTL(f)
    else:
        mesh=FileHandler.loadBinarySTL(f)
       
    ## Start of tweaking.
    if args.verbose:
        print("Calculating the optimal orientation:\n  {}\n"
                        .format(args.inputfile.split("\\")[-1]))
    try:
        cstime = time.time()
        x=Tweak(mesh, args.bi_algorithmic, args.verbose, args.angle)          
    except (KeyboardInterrupt, SystemExit):
        print("\nError, tweaking process failed!")
        raise
        
    ## List tweaking results
    if args.result or args.verbose:
        print("\nResult-stats:")
        print(" Tweaked Z-axis: \t{}".format((x.Zn)))
        print(" Axis, angle:   \t{v}, {phi}".format(v=x.v, phi=x.phi))
        print(""" Rotation matrix: 
    {:2f}\t{:2f}\t{:2f}
    {:2f}\t{:2f}\t{:2f}
    {:2f}\t{:2f}\t{:2f}""".format(x.R[0][0], x.R[0][1], x.R[0][2],
                                  x.R[1][0], x.R[1][1], x.R[1][2], 
                                  x.R[2][0], x.R[2][1], x.R[2][2]))
        print(" Unprintability: \t{}".format(x.Unprintability))
        
        print("\nFound result:    \t{:2f} s".format(time.time()-cstime))
        if args.result: 
            sys.exit()   
        
    ## Creating tweaked output file
    if x.Zn==[0,0,1]:
        tweakedcontent=mesh
    else:
        tweakedcontent=FileHandler.rotate(x.R, mesh, args.inputfile)
  
    # Support structure suggestion can be used for further applications        
    if x.Unprintability > 8:
        tweakedcontent+=" {supportstructure: yes}"
    with open(args.outputfile,'w') as outfile:
        outfile.write(tweakedcontent)
        
    ## Success message
    if args.verbose:
        print("Tweaking took:  \t{:2f} s".format(time.time()-stime))
        print("\nSuccessfully Rotated!")
