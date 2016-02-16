# STL-tweaker
The STL-tweaker is a python module which finds an optimal orientation for a 3D object on the printing platform to improve the efficiency of the 3D-print. 


Author: Christoph Schranz, Salzburg Research Forschungsgesellschaft mbH 

Date: 	12.01.2016 

Published: www.salzburgresearch.at 


Install required modules: 

The STL-tweaker is fully implemented in python 2.7 

Linux: 	apt-get install python-pip  

Linux:	 pip install numpy 

Windows: view https://pip.pypa.io/en/latest/installing/ 

Windows: pip install -i https://pypi.binstar.org/carlkl/simple numpy 


pip install python-utils 

pip install python-utils --upgrade 

pip install numpy-stl 



Testing modules in command line:  

stl2ascii <yourobject.slt>  

More infos and licences for this package at https://github.com/WoLpH/numpy-stl  



Usage:  

stl_tweaker.py must be executable.  

<STL-tweaker.py> <yourobject.stl> [optional: <int(yourownangle)>]  

