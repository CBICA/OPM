# OPM
### Openslide patch manager: parallel reading/writing of patches.

## Installation: 
```
git clone https://github.com/grenkoca/opm/tree/KimLab.git
cd OPM/
pip install -r requirements.txt
```

## Usage
To try an example:
```
python mine_patches.py images/example_slide.svs output/
```
By default it detects tissue and extracts 1000 random patches from the included .svs file. Play with this number as well as the number of parallel threads in example.py (default patches=1000, default threads=100)
## Options
There are also a handful of useful options:
- `SHOW_MINED`: shows attempted patch extractions after patches are determined. Note: this does not neccesarily show *successful* patch extractions, only attempted ones. 
- `SHOW_VALID`: show where valid indices for patch extractions are. Each index is the top-left corner of the patch. 
- `READ_TYPE`: either 'sequential' or 'random'. If sequential, it repeatedly takes the top-leftmost valid index until quota is met or the slide is saturated. If random, it randomly samples a patch from the valid indices until saturated or the quota is hit.

... and various other parameters such as patch size, thumbnail/valid mask scale, and masking thresholds.

## Workflow
OPM follows the following workflow:

<img src="OPM Flowchart.png" alt="Workflow for Open Patch Miner" width="600"/>

## Project Structure
```
.
├── mine_patches.py
├── images
│   └── example_slide.svs
├── README.md
├── requirements.txt
└── src
    ├── config.py
    ├── convert_to_tiff.py
    ├── patch_manager.py
    ├── patch.py
    └── utils.py

````
