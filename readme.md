![header-image](http://coddingtonbear-public.s3.amazonaws.com/github/barbari/header.jpg)

# Barbari: An automation script for generating milling gcode via Flatcam

I use a cheap 1610 CNC machine, KiCad, and Flatcam for milling PCBs, but remembering exactly which settings to use for each page in Flatcam for generating my milling gcode is a pain, and I occasionally mistype important values (they're almost all important!).  This flatcam automation script is intended to eliminate that problem by taking my memory and observation skills out of the equation.

## Requirements

- Flatcam: `Beta` branch (tested with 8.994)

## Use

Export your gerber & drill files:

1. Place the auxiliary axis for your board in the lower-left corner of
your board. ![](https://coddingtonbear-public.s3-us-west-2.amazonaws.com/github/barbari/instructions_gerber_aux_axis.png)
2. Open the plot settings dialog from "File", "Plot". ![](https://coddingtonbear-public.s3-us-west-2.amazonaws.com/github/barbari/instructions_gerber_plot.png)
3. Set plot settings as shown below, then click "Plot"; ![](https://coddingtonbear-public.s3-us-west-2.amazonaws.com/github/barbari/instructions_gerber_plot_settings.png) specifically make sure that you're:
   - Plotting the F.Cu, B.Cu, and Edge.Cuts layers
   - "Use auxiliary axis as origin" is checked.
4. Click the "Generate Drill Files..." button. ![](https://coddingtonbear-public.s3-us-west-2.amazonaws.com/github/barbari/instructions_gerber_drill_button.png)
5. Set the drill settings as shown below, and click "Generate drill file"; ![](https://coddingtonbear-public.s3-us-west-2.amazonaws.com/github/barbari/instructions_gerber_drill_settings.png) specifically make sure that you've set the following settings correctly:
   - Exporting in the "Excellon" file format.
   - "PTH and NPTH in a single file" is checked.
   - Drill Origin is set to "Auxiliary axis"
   - Drill Units is set to "Millimeters"
6. Make note of the path to which these files were written for use below as `/path/to/gerber/exports`.  ![](https://coddingtonbear-public.s3-us-west-2.amazonaws.com/github/barbari/instructions_gerber_path_gerber.png) ![](https://coddingtonbear-public.s3-us-west-2.amazonaws.com/github/barbari/instructions_gerber_path_drill.png)
6. Close the displayed dialogs.

Generate your flatcam script:

```
barbari build /path/to/gerber/exports simple
```

"simple" in the above string is the name of the milling configuration to use for the generated flatcam script. Alternative options exist -- see "Configuration" below for details.

Run your script in flatcam:

1. From Flatcam, open the "File", "Scripting", "Run Script".  ![](https://coddingtonbear-public.s3-us-west-2.amazonaws.com/github/barbari/instructions_flatcam_menu.png)
2. Select the script generated in `/path/to/gerber/exports`.

Run your generated gcode in whatever tool you use for sending gcode to your mill.  Note that the files will be stored in `/path/to/gerber/exports` and are expected to be run in the order indicated by their file names.

## Configuration

Barbari comes packaged with a couple milling profiles for two fairly conservative sets of milling operations; more than likely, the "simple" profile will be enough for you, but if it's not, you can either use one of the other packaged configuration settings (see `list-configs` and `display-config` to see their details) or create your own by exporting an example configuration and modifying it (see `generate-config`).

Note that Barbari configuration files can be layered atop one another by providing more than a single configuration file.  Properties defined in later configuration files take precedence over properties in earlier ones, and drilling profiles are merged together.

See `--help` for more information.
