![header-image](http://coddingtonbear-public.s3.amazonaws.com/github/barbari/header.jpg)

# Barbari: An automation script for generating milling gcode via Flatcam

I use a cheap 1610 CNC machine, KiCad, and Flatcam for milling PCBs, but remembering exactly which settings to use for each page in Flatcam for generating my milling gcode is a pain, and I occasionally mistype important values (they're almost all important!).  This flatcam automation script is intended to eliminate that problem by taking my memory and observation skills out of the equation.

## Use

Run with flatcam via:

```
    barbari build /path/to/gerber/exports
    flatcam --shellfile=/path/to/gerber/exports/flatcam_shell
```

## Configuration

By default, Barbari is configured to generate fairly conservatively
millable PCBs, and makes a handful of assumptions about how you might
want to drill your PCB; you can override these configurations by

1. Generating a configuration file by running `barbari generate_config`
2. Editing the file at the path displayed.
