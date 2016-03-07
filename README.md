# STL-tweaker
##The STL-tweaker is a auto-rotate module which finds the STL object's optimal orientation in the printing platform to improve the efficiency of the 3D print.

Author: Christoph Schranz, 12.01.2016 


## Installing required modules:
If your STL file is written in [ascii](https://de.wikipedia.org/wiki/STL-Schnittstelle#ASCII-Format), you can start tweaking!

Otherwise, you have to install the following packages:

Linux: 	
```bash
apt-get install python-pip

pip install numpy
```

Windows: [pip under windows](https://pip.pypa.io/en/latest/installing/)

`pip install -i https://pypi.binstar.org/carlkl/simple numpy` 


```bash
pip install python-utils 

pip install numpy-stl 
```

Testing module:

`stl2ascii <yourobject.stl> ` 

[More infos:](https://github.com/WoLpH/numpy-stl)  


## Quickstart:  

FileHandler.py must be executable.  

`FileHandler.py yourobject.stl [optional: int(yourownangle)]`

