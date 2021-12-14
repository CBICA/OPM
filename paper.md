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
    affiliation: 2
  - name: Siddhesh Thakur
    orcid: 0000-0003-4807-2495
    affiliation: 2
  - name: Spyridon Bakas
    orcid: 0000-0001-8734-6482
    affiliation: 2
affiliations:
 - name: National Human Genome Research Association (NHGRI), National Institutes of Health (NIH), 31 Center Dr, Bethesda, MD 20894
   index: 1
 - name: Center for Biomedical Image Computing and Analytics (CBICA), University of Pennsylvania, Philadelphia, PA, USA
   index: 2
date: 13 December 2021
bibliography: paper.bib

---

# Summary

The transition of histopathology from analog to digital has opened the world 
of medicine to new classes of algorithms aimed at aiding typical pathological
analysis. Histopathology images can be gigapixel sized, rendering loading 
the whole image into memory is typically infeasible. To work around this
limitation, researchers typically extract small square sections of the whole slide
in order to train algorithms. 


# Statement of need

Despite patch extraction being requisite for applying algorithms to digital 
pathology, there are very few applications which automatically generate small patches
from the entire image. Additionally, accompanying information must be saved with patches.
This includes, but is not limited to, the coordinates of patches, the associated patient 
information, corresponding segmentation maps, and pixel classes represented in the patches.

Open Patch Miner (OPM) provides a high-level library capable of tissue detection, 
parallel patch extraction, validation, and saving of patches. It has a modular nature, allowing 
for users to define custom checks to determine which patches should be saved, and where patches
should be mined from. Additionally, OPM can automatically determine candidate regions to call
patches from and will mine either a predetermined number of patches, or will mine until no more 
patches can be called without the allowed overlap.


# Method

![Open Patch Miner has the following general workflow.\label{fig:flowchart}](./images/opm_flowchart.png)

Once initialized, OPM begins by masking out background whitespace, pen markings, and other artifacts 
as defined by user settings. This generates a binary mask of valid/invalid candidate regions. 
Next, the desired number of patches are read, and each patch is passed through a series of user-defined
checks. If a patch passes all checks, it is saved and the associated information is recorded. If not, 
the patch is rejected. If either the required number of patches have been saved or no more candidate pixels
exit, OPM exits. If the patch quota has not been achieved and there is still potential regions 
for patch extraction, OPM will resume. If there are no more candidate patches, OPM will determine the 
slide is saturated and exit. The overall flowchart is illustrated in \autoref{fig:flowchart}.


# Acknowledgements

We acknowledge contributions from Caleb Grenko, Sarthak Pati, Siddhesh Thakur, and Spyridon Bakas.
