# STL-tweaker
##The STL-tweaker is an auto-rotate module which finds the STL object's optimal orientation on the printing platform to improve the efficiency of the 3D print.

Author: Christoph Schranz, 12.01.2016 

[STL-tweaker](http://www.salzburgresearch.at/blog/3d-print-positioning/)

## Quickstart:  

Executable FileHandler.py works on ascii STL.

`FileHandler.py yourobject.stl [optional: int(yourownangle)]`

## Installing optional modules:  (for binary STL)
If your STL file is written in [ascii](https://de.wikipedia.org/wiki/STL-Schnittstelle#ASCII-Format), you can start tweaking!

Otherwise, you have to convert it (e.g. per webservice) or install the following packages:

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

More about [numpy-stl](https://github.com/WoLpH/numpy-stl).

