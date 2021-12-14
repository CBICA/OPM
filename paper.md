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
the whole image into memory is typically infeasible. To compensate for these
large sizes, most algorithms resort to using small patches called from the images.
Despite patch extraction being requisite for applying algorithms to digital pathology,
there are very few applications capable of easy patch extraction while still 
allowing for user-defined processes and checks. Open Patch Miner (OPM) provides a 
high-level library capable of tissue detection, parallel patch extraction, 
validation, and saving. Additionally, OPM's modular design allows for user-defined
algorithms for tissue detection and patch validation.

# Statement of need

`Gala` is an Astropy-affiliated Python package for galactic dynamics. Python
enables wrapping low-level languages (e.g., C) for speed without losing
flexibility or ease-of-use in the user-interface. The API for `Gala` was
designed to provide a class-based and user-friendly interface to fast (C or
Cython-optimized) implementations of common operations such as gravitational
potential and force evaluation, orbit integration, dynamical transformations,
and chaos indicators for nonlinear dynamics. `Gala` also relies heavily on and
interfaces well with the implementations of physical units and astronomical
coordinate systems in the `Astropy` package [@astropy] (`astropy.units` and
`astropy.coordinates`).

`Gala` was designed to be used by both astronomical researchers and by
students in courses on gravitational dynamics or astronomy. It has already been
used in a number of scientific publications [@Pearson:2017] and has also been
used in graduate courses on Galactic dynamics to, e.g., provide interactive
visualizations of textbook material [@Binney:2008]. The combination of speed,
design, and support for Astropy functionality in `Gala` will enable exciting
scientific explorations of forthcoming data releases from the *Gaia* mission
[@gaia] by students and experts alike.

# Mathematics

# Citations

Citations to entries in paper.bib should be in
[rMarkdown](http://rmarkdown.rstudio.com/authoring_bibliographies_and_citations.html)
format.

If you want to cite a software repository URL (e.g. something on GitHub without a preferred
citation) then you can do it with the example BibTeX entry below for @fidgit.

For a quick reference, the following citation commands can be used:
- `@author:2001`  ->  "Author et al. (2001)"
- `[@author:2001]` -> "(Author et al., 2001)"
- `[@author1:2001; @author2:2001]` -> "(Author1 et al., 2001; Author2 et al., 2002)"

# Figures

Figures can be included like this:
![Caption for example figure.\label{fig:example}](figure.png)
and referenced from text using \autoref{fig:example}.

Figure sizes can be customized by adding an optional second parameter:
![Caption for example figure.](figure.png){ width=20% }

# Acknowledgements

We acknowledge contributions from Brigitta Sipocz, Syrtis Major, and Semyeong
Oh, and support from Kathryn Johnston during the genesis of this project.

# References
