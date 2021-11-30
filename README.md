Overview
========

This repo contains a Python program used to generate star charts in SVG format
for the design of a banner page for The Ecliptic, the newsletter of
the Lackawanna Astronomical Society, closing on 2021-11-30. Also included are
other files relevant to the contest submission.

The star chart is rendered in ecliptic coordinates in a simple plate carrée
projection. The constellation figures are from Stellarium and the star data
is from the Hipparcos catalog. Neither of these is present in the repository
and must be downloaded as indicated below.

The ecliptic is drawn as a dashed line that renders the message
"THE ECLIPTIC -- LACKAWANNA ASTRONOMICAL SOCIETY" in Morse code.

Setup
=====

The program is written for Python 3.9.3 and requires the svgwrite package
('pip install svgwrite').

The Stellarium constellation figures file is downloaded from
https://github.com/Stellarium/stellarium/blob/master/skycultures/western_SnT/constellationship.fab
(click "RAW" to download the file.)
This is the Sky&Telescope version of the constellation figures.
There are other versions available in the
https://github.com/Stellarium/stellarium/blob/master/skycultures source tree.

To find the star catalog, search for "Hipparcos New Astrometric Catalog"
- One of the matches is
https://heasarc.gsfc.nasa.gov/W3Browse/star-catalog/hipnewcat.html
- From there, the first link under References is
https://ui.adsabs.harvard.edu/abs/2007A%26A...474..653V/abstract
- **(Note: the above are included to document how the data was found.
You can go directly to the URL below.)**
- On that page, click "CDS (2)" under "DATA PRODUCTS" to get to
https://cdsarc.cds.unistra.fr/viz-bin/cat/I/311  
- On that page, click FTP
- Then, ReadMe gives a description of the record layout
- And, hip2.dat.gz is the star catalog file that we need.
The program decompresses it on the fly so it can be
kept in the compressed ".gz" format.


