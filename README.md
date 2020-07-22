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
By default it detects tissue and extracts 1000 random patches from the included .svs file. Play with this number as well as the number of parallel threads in example.py (default patches=1000, default threads=100)
```
.
├── example.py
├── images
│   └── example_slide.svs
├── README.md
├── requirements.txt
└── src
    ├── config.py
    ├── convert_to_tiff.py
 `   ├── patch_manager.py
    ├── patch.py
    └── utils.py

````
