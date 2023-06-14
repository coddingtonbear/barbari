![header-image](http://coddingtonbear-public.s3.amazonaws.com/github/barbari/header.jpg)

# Barbari: An automation script for generating milling gcode via Flatcam

I use a cheap 1610 CNC machine, KiCad, and Flatcam for milling PCBs, but remembering exactly which settings to use for each page in Flatcam for generating my milling gcode is a pain, and I occasionally mistype important values (they're almost all important!).  This flatcam automation script is intended to eliminate that problem by taking my memory and observation skills out of the equation.

## Requirements

- Flatcam: `Beta` branch (tested with 8.994)

## Quickstart

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
barbari build-script /path/to/gerber/exports simple
```

"simple" in the above string is the name of the milling configuration to use for the generated flatcam script. Alternative options exist -- see "Configuration" below for details.

Run your script in flatcam:

1. From Flatcam, open the "File", "Scripting", "Run Script".  ![](https://coddingtonbear-public.s3-us-west-2.amazonaws.com/github/barbari/instructions_flatcam_menu.png)
2. Select the script generated in `/path/to/gerber/exports`.

Run your generated gcode in whatever tool you use for sending gcode to your mill.  Note that the files will be stored in `/path/to/gerber/exports` and are expected to be run in the order indicated by their file names.

## How does milling a PCB work?

Roughly, the process is handled via the following steps:

1. Milling Alignment holes (`alignment_holes` in the configuration).  These are used to allow you to perfectly flip your PCB for milling on both sides.
2. Isolation routing (`isolation_routing` in the configuration).  This will route your PCB's traces on both sides of the board.  First, the back of your PCB (`B.Cu`) is routed, then the front (`F.Cu`).  You'll want to flip over your board, using the drilled alignment holes in between these two steps.
3. Drilling (`drill` in the configuration).
4. Milling slots (`slot` in the configuration).
5. Edge cuts (`edge_cuts` in the configuration). This is for cutting your PCB out of the larger piece of copper-clad board.

## Configuration

Barbari comes packaged with a couple milling profiles for two fairly conservative sets of milling operations; more than likely, the "simple" profile will be enough for you, but if it's not, you can either use one of the other packaged configuration settings (see `list-configs` and `display-config` to see their details) or create your own by exporting an example configuration and modifying it (see `generate-config`).

Note that Barbari configuration files can be layered atop one another by providing more than a single configuration file.  Properties defined in later configuration files take precedence over properties in earlier ones, and drilling profiles are merged together.

### Sections

Your configuration file is divided into multiple sections for the various steps of the milling process.  Those sections are used for generating instructions for Flatcam.

Note that all properties use metric units -- usually `millimeters` unless specifically noted.

#### `description`

This is a short string describing this milling profile, and is used only for display in Barbari.

#### `alignment_holes`

This is used to allow you to perfectly flip your PCB for milling on both sides.

Example:

```yaml
alignment_holes:
  hole_size: 3.4
  hole_offset: 1
  tool_size: 1.5
  cut_z: -10
  travel_z: 2
  feed_rate: 100
  spindle_speed: 12000
  multi_depth: true
  depth_per_pass: 0.2
```

#### `isolation_routing`

This is used to route the traces on your board.

Example:

```yaml
isolation_routing:
  tool_size: 0.18
  width: 1
  pass_overlap: 0.5
  cut_z: -0.2
  travel_z: 2
  feed_rate: 200
  spindle_speed: 12000
  multi_depth: true
  depth_per_pass: 0.1
```

#### `drill`

You probably don't have as many bits on hand as a PCB board house will; so these sections are here to allow you to group multiple drill sizes into sets of processes.  For example, if you had only three bits -- a 0.4mm drill for vias, a 1.0mm drill for most through-holes, and a 1.0mm mill for everything bigger than that, you could have a section like this:

```yaml
drill:
  via:
    max_size: 0.4
    specs:
    - type: cnc_drill
      params:
        tool_size: 0.4
        drill_z: -2.5
        travel_z: 2
        feed_rate: 50
        spindle_speed: 12000
  drilled:
    min_size: 0.4
    max_size: 1.0
    specs:
    - type: cnc_drill
      params:
        tool_size: 1.0
        drill_z: -2.5
        travel_z: 2
        feed_rate: 50
        spindle_speed: 12000
  milled:
    min_size: 1.0
    specs:
    - type: mill_holes
      params:
        tool_size: 1
        cut_z: -2.5
        travel_z: 2
        feed_rate: 100
        spindle_speed: 12000
        multi_depth: true
        depth_per_pass: 0.2
```

You'll see from the above that any holes up to 0.4mm in diameter will be drilled using the `via` processes (called `specs` here) -- drilling with a 0.4mm drill, any drills from 0.4mm to 1.0mm in size will be drilled using a 1.0mm drill bit, and anything bigger than 1.0mm will be milled using a 1.0mm end mill.  You might
notice that some drill bit sizes match multiple specs -- that's fine -- barbari
will choose the best process for each particular tool algorithmically.

In some situations -- mostly around drilling large holes -- you might need a particular range of drill sizes to be drilled more than once.  For example, the included drilling profile for using [voltera 1mm rivets](https://www.voltera.io/store/consumables/rivets-1-0mm) for plated through-holes looks like this:

```yaml
  pth:
    min_size: 0.4
    max_size: 1.1
    specs:
    - type: cnc_drill
      params:
        tool_size: 0.7
        drill_z: -2.5
        travel_z: 2
        feed_rate: 50
        spindle_speed: 12000
    - type: cnc_drill
      params:
        tool_size: 1.5
        drill_z: -2.5
        travel_z: 2
        feed_rate: 50
        spindle_speed: 12000
```

The above configuration will drill any holes from 0.4mm to 1.1mm in diameter twice -- first with a 0.7mm drill, and then afterward with a 1.5mm drill.

#### `slot`

The slot section defines job parameters for milling slots in your PCB (i.e. non-round holes).  It follows exactly the same pattern used for `drill` above.

#### `edge_cuts`

You probably won't be using an entire sheet of copper-clad board for your board.  This section defines how to cut your newly-milled PCB out of the copper-clad.


#### `include`

This section is special, and is used for including _other_ configuration files into the configuration file.  It is a list of strings that can be either:

- A relative (to the configuration file) path to a different configuration file to include.  This must end in `.yaml` or `.yml`.  This is the method to use if you *would not* like user-level configurations to override the pre-packaged ones.
- The name of a configuration to use.  See `list-configs --all` for a list of configuration files.  This is the method to use if you *would* like user-level configurations to override the pre-packaged ones.

For example, this is the "rivets" configuration:

```yaml
description: |
  The standard configuration @coddingtonbear
  uses when milling his PCBs.  This uses
  copper wire vias, 10mm deep alignment holes, [voltera 1mm rivets](https://www.voltera.io/store/consumables/rivets-1-0mm)
  for holes near 1mm, and milled holes
  larger than 1.1mm.
include:
  - ./default_isolation_routing.yaml
  - ./default_alignment_holes.yaml
  - ./copper_wire_vias.yaml
  - ./drilled_pth_04_11.yaml
  - ./milled_11.yaml
  - ./default_edge_cuts.yaml
```
