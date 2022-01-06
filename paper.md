---
title: 'Open Patch Miner: parallel reading/writing of patches for digital histopathology'
tags:
  - Python
  - histopathology
  - open
  - patch
  - miner
  - patches
authors:
  - name: Caleb M. Grenko
    orcid: 0000-0002-3926-5503
    affiliation: "1, 2" # (Multiple affiliations must be quoted)
  - name: Sarthak Pati
    orcid: 0000-0003-2243-8487
    affiliation: "1, 2, 3, 4"
  - name: Siddhesh Thakur
    orcid: 0000-0003-4807-2495
    affiliation: "1, 2"
  - name: Spyridon Bakas
    orcid: 0000-0001-8734-6482
    affiliation: "1, 2, 3"
affiliations:
  - name: Center for Biomedical Image Computing and Analytics (CBICA), University of Pennsylvania, Philadelphia, PA, USA  
    index: 1
  - name: Department of Pathology and Laboratory Medicine, Perelman School of Medicine, University of Pennsylvania, Philadelphia, PA, USA  
    index: 2
  - name: Department of Radiology, Perelman School of Medicine, University of Pennsylvania, Philadelphia, PA, USA  
    index: 3
  - name: Department of Informatics, Technical University of Munich, Munich, Bavaria, Germany  
    index: 4
date: 20 December 2021
bibliography: paper.bib

---

# Summary

The transition of histopathology from glass slides to digitized whole slide images (WSIs) has opened the world of medicine to new classes of computational algorithms aimed at aiding routine clinical pathological analysis. The size of WSIs can be quite large, which means that rendering the whole image into memory at once is typically infeasible. To work around this limitation, researchers typically extract small square sections (i.e. patches) of the whole slide in order to train algorithms. 


# Statement of need

Despite patch extraction being requisite for applying algorithms to digital histopathology, there are very few applications which automatically generate small patches from the entire WSI, which is a critical first step during computational histopathology analysis [@gurcan2009histopathological; @tizhoosh2018artificial]. Additionally, accompanying information and relevant metadata must be saved with patches [@hou2016patch; @cui2021artificial]. This includes, but is not limited to, the coordinates of patches, the associated patient information, corresponding segmentation maps, and pixel classes represented in the patches. 

Open Patch Miner (OPM) provides a high-level library capable of tissue detection, parallel patch extraction, validation, and saving of patches. It has a modular nature, allowing for users to define custom checks to determine which patches should be saved, and where patches should be extracted from. Additionally, OPM can automatically determine candidate tissue regions and will save either a predetermined number of patches, or will extract patches until no more can be called without the allowed overlap. Currently, OPM is used in the Generally Nuanced Deep Learning Framework (GaNDLF) [@pati2021gandlf] to extract patches from a WSI for training neural networks. Additionally, OPM has been used in currently published studies with applications in histopathology normalization [@grenko2020norm], prediction of overall survival of glioblastoma patients [@hao2020prediction], and the longitudinal analysis of recurrent glioma to better understand the underlying genetics and tumor microenvironment [@varn2021longitudinal; @varn2021epco].


# Method

![Open Patch Miner has the following general workflow.\label{fig:flowchart}](./images/OPM_flowchart.png)

Once initialized, OPM begins by masking out background whitespace, pen markings, and other artifacts as defined by user settings. This generates a binary mask which defines the valid candidate regions within the image. Next, the desired number of patches are read, and each patch is passed through a series of user-defined checks. If a patch passes all checks, it is saved along with all associated information. This process continues until either the required number of patches have been saved or no more patches exist in the valid candidate regions of the image. Additionally, if the user inputs a pre-existing .csv of coordinates along with a slide, OPM will extract patches from the locations defined in the csv. The overall flowchart is illustrated in \autoref{fig:flowchart}. Towards this end, OPM offers a robust, reproducible, comprehensive solution to researchers working on the field of computational pathology.


# Acknowledgements

This work was partly supported by the National Institutes of Health (NIH) under award number NIH/NCI:U01CA242871.


# References
