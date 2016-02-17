# STL-tweaker
The STL-tweaker is a STL object positioning tool implemented as python module which finds an optimal orientation for a 3D object on the printing platform to improve the efficiency of the 3D-print. 


Author: Christoph Schranz, Salzburg Research 

Date: 	12.01.2016 


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

`stl2ascii <yourobject.slt> ` 

[More infos:](https://github.com/WoLpH/numpy-stl)  


## Quickstart:  

stl_tweaker.py must be executable.  

`path/STL-tweaker.py path/yourobject.stl [optional: int(yourownangle)]`

