# OPM
### Openslide patch manager: parallel reading/writing of patches.

Installation: 
```
git clone https://github.com/grenkoca/OPM.git
cd OPM/
pip install -r requirements.txt
```
To try an example:
```
python example.py images/example_slide.svs output/
```
By default it generates 500 random patches from the included .svs file. Play with this number as well as the number of parallel threads in example.py (default patches=500, default threads=50)
```
.
├── images
│   └── example_slide.svs
├── README.md
└── src
    ├── example.py 
    ├── patch_manager.py
    └── patch.py 
````
