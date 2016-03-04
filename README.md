# STL-tweaker
##The STL-tweaker is a auto-rotate module which finds the STL object's optimal orientation in the printing platform to improve the efficiency of the 3D print.

Author: Christoph Schranz, 12.01.2016 


## Installing required modules:

The STL-tweaker is fully implemented in python 2.7 

Linux: 	`apt-get install python-pip`

Linux:	 `pip install numpy` 

Windows: [pip under windows](https://pip.pypa.io/en/latest/installing/)

Windows: `pip install -i https://pypi.binstar.org/carlkl/simple numpy` 


```bash
pip install python-utils 

pip install python-utils --upgrade 

pip install numpy-stl 
```


## Testing modules in command line:  

`stl2ascii <yourobject.stl> ` 

[More infos:](https://github.com/WoLpH/numpy-stl)  


## Quickstart:  

FileHandler.py must be executable.  

`FileHandler.py yourobject.stl [optional: int(yourownangle)]`

