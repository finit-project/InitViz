# InitViz

<a href="doc/initviz.png"><img align="right" src="doc/initviz.png" width=350 title="InitViz Screenshot"></a>

Boot and init process performance visualization tool.

## Overview

InitViz visualizes system boot and init process performance by
collecting and rendering detailed timing data.  It consists of
two components:

- `bootchartd`: Data collector that runs during boot
- `initviz`: Interactive and batch visualization tool

## Quick Start

### Profiling Boot

Add to kernel command line (e.g., `/boot/grub/grub.cfg`):

```
initcall_debug printk.time=y quiet init=/sbin/bootchartd
```

After boot, data is saved to `/var/log/bootchart.tgz`.

### Viewing Results

Interactive mode:

```bash
initviz -i /var/log/bootchart.tgz
...
```

Generate PNG:

```bash
initviz -f png -o bootchart.png /var/log/bootchart.tgz
...
```

### Profiling Running System

```bash
bootchartd start
# ... do something ...
bootchartd stop
initviz -i /var/log/bootchart.tgz
```

## Features

- High-resolution timing (nanosecond precision via taskstats)
- Interactive viewer with zoom and pan
- Export to PNG, SVG, or PDF
- Process tree with CPU and I/O wait visualization
- Event annotation support
- Configurable process filtering

## Requirements

- Linux kernel with `CONFIG_PROC_EVENTS=y` and `CONFIG_TASKSTATS=y` (recommended)
- Python 3
- GTK 3 (for interactive mode)
- Cairo (for rendering)

## Installation

```bash
make
sudo make install
```

## Command Line Options

```
initviz [options] PATH

Options:
  -i, --interactive         Start in interactive mode
  -f, --format FORMAT       Output format: png, svg, pdf (default: png)
  -o, --output PATH         Output file or directory
  -n, --no-prune            Don't prune process tree
  -q, --quiet               Suppress informational messages
  -t, --boot-time           Display boot time only (text)
  --show-pid                Show process IDs
  --show-all                Show full process details
  --crop-after PROCESS      Crop chart after PROCESS starts
  --annotate PROCESS        Annotate when PROCESS starts
  --annotate-file FILE      Write annotation timestamps to FILE
```

## History

InitViz is a fork of [bootchart2](https://github.com/xrmx/bootchart) by
Riccardo Magliocchetti, which combined the original bootchart shell script
by Ziga Mahkovec with pybootchartgui by Anders Norgaard and Henning Niss,
and a C-based collector by Scott James Remnant and Michael Meeks.

## License

The visualization tool (initviz.py) is licensed under GPLv3+. The collector
(bootchartd) is licensed under GPLv2. See COPYING and individual source files
for details.
