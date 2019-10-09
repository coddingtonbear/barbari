# Barbari: An automation script for generating milling gcode via Flatcam

*This is a work in progress*

I use a cheap 1610 CNC machine, KiCad, and Flatcam for milling PCBs, but remembering exactly which settings to use for each page in Flatcam for generating my milling gcode is a pain, and I occasionally mistype important values (they're almost all important!).  This flatcam automation script is intended to eliminate that problem by taking my memory and observation skills out of the equation.

## Goals:

Run with flatcam via:

```
    barbari /path/to/gerber/exports
    flatcam --shellfile=/path/to/gerber/exports/barbari.flatcam_shell
```

Intentions are that this will:

* [ ] Automatically generate alignment drills of a configurable size for lining-up the F.Cu and B.Cu layers, including mirroring the B.Cu layer.
* [ ] Instruct flatcam to generate the proper gcode for each copper layer.
* [ ] Instruct flatcam to generate the proper gcode for each drill layer, grouping drills into configurable groups for Vias, PTH, and NPTH holes.
* [ ] Configurable via a dotfile somewhere.
* [ ] *Stretch* Maybe join all of the gcode files together into a single one having tool change commands separating relevant steps (easy on the drill side; harder on the copper side).
