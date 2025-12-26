Change Log
==========

All relevant changes are documented in this file.


[UNRELEASED][] - InitViz
------------------------

InitViz is a fork of [bootchart2][] by Riccardo Magliocchetti.

### Changes
- Rename project from bootchart2 to InitViz
- Rename `pybootchartgui` to `initviz`
- Add interactive mode with Best Fit feature
- Convert man pages to mdoc format
- Reorganize documentation to `doc/` and `man/` directories
- Drop systemd service files (use `systemd-analyze` instead)
- Change distribution format from tar.bz2 to tar.gz

### Fixes
- Fix buffer overflow in collector with `snprintf()` replacements
- Replace all unsafe `sprintf()` calls with `snprintf()`


[0.14.9][] - 2020-01-05
-----------------------

### Changes
- **bootchartd:** Make python3 the default Python, by Riccardo
- **bootchartd:** Add sddm-helper to EXIT_PROC, by arucard21
- **pybootchartgui:** Hide interactive option on Python3, by Riccardo

### Fixes
- **bootchartd:** Fix memory corruption, by mephi42
- **bootchartd:** Unblock SIGTERM, by mephi42
- **bootchartd:** Fix compilation with gcc-6, by Riccardo
- **bootchartd:** Fix BOOTLOG_DEST default value, by Steffen Pankratz
- **bootchartd:** Add missing include, by Mike Frysinger
- **bootchartd:** Ignore SIGHUP when starting as PID 1, by mephi42
- **bootchartd:** Add missing include, by Georges Savoundararadj
- **pybootchartgui:** Avoid division by zero, by mephi42
- **pybootchartgui:** Make parsing more robust against non utf-8 bytes, by AzureCrimson
- **pybootchartgui:** Make it work with Python3.8, by Pops Dylan
- **pybootchartgui:** Fix tests warnings, by Riccardo


[0.14.8][] - 2017-07-23
-----------------------

### Changes
- **pybootchartgui:** Use half the memory when parsing files, by Andrey Bondarenko

### Fixes
- **bootchartd:** Misc collector fixes, by mephi42
- **bootchartd:** Fix for sparc, by Eric Saint Etienne


[0.14.7][] - 2016-12-05
-----------------------

### Changes
- **bootchartd:** Use /bin/sh instead of bash, by Robert Yang

### Fixes
- **bootchartd:** Misc coverity fixes, by Riccardo
- **bootchartd:** Fix systemd regression, by Max Eliaser
- **pybootchartgui:** Fix merging of logger process #56, by Riccardo


[0.14.6][] - 2016-07-10
-----------------------

### Changes
- **bootchartd:** Add lightdm-gtk-greeter to EXIT_PROC, by Paul Menzel
- **bootchartd:** Make component naming and paths more flexible, by Simon McVittie
- **bootchartd:** Support cross compilation, build fixes, code cleanup, by Sangjung Woo
- **bootchartd:** Respect CC environment variable, by Max Eliaser

### Fixes
- **collector:** Misc collector fixes, by Matthew Sanderson
- **collector:** Fix collector without taskstats, by Max Eliaser
- **collector:** Fix collector for non debug builds, by Max Eliaser
- **pybootchartgui:** Fix --annotate-file, by Riccardo
- **pybootchartgui:** More robust meminfo parsing, by Riccardo
- **pybootchartgui:** Skip proc_stat.log entries without any times, by David Kruger


[0.14.5][] - 2015-04-26
-----------------------

### Fixes
- **pybootchartgui:** Fix tests with python3, by Riccardo
- **pybootchartgui:** Fix parsing of files with non-ascii bytes, by Riccardo
- **pybootchartgui:** Robustness fixes to taskstats and meminfo parsing, by Riccardo
- **pybootchartgui:** More python3 fixes, by Riccardo


[0.14.4][] - 2015-02-02
-----------------------

### Changes
- **bootchartd:** Add relevant EXIT_PROC for GNOME3, XFCE4, openbox, by Justin Lecher and Ben Eills

### Fixes
- **pybootchartgui:** Fix some issues in --crop-after and --annotate, by Riccardo
- **pybootchartgui:** Fix pybootchartgui process_tree tests, by Riccardo
- **pybootchartgui:** More python3 fixes, by Riccardo


[0.14.2][] - 2014-08-17
-----------------------

### Fixes
- **pybootchartgui:** Fix some crashes in parsing.py, by Jakub Czaplicki and Riccardo
- **pybootchartgui:** Speedup meminfo parsing, by Riccardo
- **pybootchartgui:** Fix indentation for python3.2, by Riccardo


[0.14.1][] - 2014-05-31
-----------------------

### Changes
- **bootchartd:** Look for bootchart_init in the environment, by Henry Gebhardt

### Fixes
- **bootchartd:** Expect dmesg only if started as init, by Henry Yei
- **pybootchartgui:** Fixup some tests, by Riccardo
- **pybootchartgui:** Support hp smart arrays block devices, by Anders Norgaard and Brian Murray
- **pybootchartgui:** Fixes for -t, -o and -f options, by Mladen Kuntner, Harald, and Riccardo


[0.14.0][] - 2013-04-14
-----------------------

### Changes
- **bootchartd:** Add ability to define custom commands, by Lucian Muresan and Peter Hjalmarsson
- **pybootchartgui:** Render cumulative I/O time chart, by Sankar P
- **pybootchartgui:** Python3 compatibility fixes, by Riccardo
- Remove confusing, obsolete setup.py, by Michael
- Install docs to /usr/share/, by Michael
- Add bootchart2, bootchartd and pybootchartgui manpages, by Francesca Ciceri and David Paleino
- Lot of fixes for easier packaging, by Peter Hjalmarsson

### Fixes
- **collector:** Fix tmpfs mount leakage, by Peter Hjalmarsson


[0.12.6][] - 2012-07-23
-----------------------

### Changes
- **bootchartd:** Better check for initrd, by Riccardo Magliocchetti
- **bootchartd:** Code cleanup, by Riccardo
- **bootchartd:** Make the list of processes we are waiting for editable in config file by EXIT_PROC, by Riccardo
- **pybootchartgui:** Add kernel bootchart tab to interactive gui, by Michael
- **pybootchartgui:** Report bootchart version in cli interface, by Michael
- **pybootchartgui:** Improve rendering performance, by Michael
- **pybootchartgui:** GUI improvements, by Michael
- **pybootchartgui:** Lot of cleanups, by Michael
- Add systemd service files, by Harald and Wulf C. Krueger

### Fixes
- **bootchartd:** Fix parsing of cmdline for alternative init system, by Riccardo
- **bootchartd:** Fixed calling init in initramfs, by Harald
- **bootchartd:** Exit 0 for start, if the collector is already running, by Harald
- **collector:** Try harder with taskstats, by Michael
- **collector:** Plug some small leaks, by Riccardo
- **collector:** Fix missing PROC_EVENTS detection, by Harald
- Do not python compile if NO_PYTHON_COMPILE is set, by Harald


[0.12.5][] - 2012-06-06
-----------------------

Administrative snafu version; pull before pushing...


[0.12.4][] - 2012-05-13
-----------------------

### Changes
- **collector:** Add meminfo polling, by Dave Martin
- **pybootchartgui:** Add process grouping in the cumulative chart, by Riccardo
- **pybootchartgui:** Prettier coloring for the cumulative graphs, by Michael
- **pybootchartgui:** Render memory usage graph, by Dave Martin

### Fixes
- **bootchartd:** Reduce overhead caused by pidof, by Riccardo Magliocchetti
- **collector:** Attempt to retry ptrace to avoid bogus ENOSYS, by Michael
- **pybootchartgui:** Handle dmesg timestamps with big delta, by Riccardo
- **pybootchartgui:** Avoid divide by zero when rendering I/O utilization, by Riccardo
- **pybootchartgui:** Fix cpu time calculation in cumulative chart, by Riccardo
- **pybootchartgui:** Get i/o statistics for flash based devices, by Riccardo
- **pybootchartgui:** Fix interactive CPU rendering, by Michael


[0.12.3][] - 2011-10-30
-----------------------

### Changes
- **collector:** Store /proc/cpuinfo in the boot-chart archive, by Riccardo

### Fixes
- **collector:** pclose after popen, by Riccardo Magliocchetti
- **collector:** Fix buffer overflow, by Riccardo
- **collector:** Count 'processor:' in /proc/cpuinfo for ARM, by Michael
- **collector:** Get model name from that line too for ARM, by Riccardo
- **collector:** Try harder to detect missing TASKSTATS, by Michael
- **collector:** Sanity-check invalid domain names, by Michael
- **collector:** Detect missing PROC_EVENTS more reliably, by Michael
- **collector:** README fixes, by Riccardo and Michael
- **pybootchartgui:** Make num_cpu parsing robust, by Michael


[0.12.2][] - 2011-02-27
-----------------------

### Fixes
- Fix pthread compile/linking bug


[0.12.1][] - 2011-02-26
-----------------------

### Changes
- **collector:** Now GPLv2
- **collector:** Add rdinit support for very early initrd tracing
- **collector:** Cleanup and re-factor code into separate modules
- **collector:** Re-factor arg parsing, and parse remote process args
- **collector:** Move much of bootchartd from shell to C
- **collector:** Drop dmesg and uname usage
- **collector:** Avoid rpm/dpkg with native version reporting
- **pybootchartgui:** Add '-t' / '--boot-time' argument, by Matthew Bauer

### Fixes
- **pybootchartgui:** Pylint cleanup
- **pybootchartgui:** Handle empty traces more elegantly
- **collector:** Handle missing bootchartd.conf cleanly


[0.12.0][] - 2010-11-07
-----------------------

### Changes
- **collector:** Use netlink PROC_EVENTS to generate parentage data
- **collector:** Finally kills any need for 'acct' et. al.
- **collector:** Removes need to poll /proc (faster)
- **collector:** Cleanup code to K&R, 8 stop tabs
- **pybootchartgui:** Consume thread parentage data


[0.11.4][] - 2010-08-22
-----------------------

### Changes
- **collector:** Dump full process path and command-line args
- **pybootchartgui:** Has a 'show more' option to show command-lines

### Fixes
- **collector:** If run inside an initrd detect when /dev is writable and remount ourselves into that
- **collector:** Overflow buffers more elegantly in extremis
- **collector:** Calm down debugging output
- **pybootchartgui:** Can render logs in a directory again


[0.11.3][] - 2010-05-09
-----------------------

### Changes
- Add process command-line display
- Enable parsing, add check button to UI, and --show-all command-line option

### Fixes
- Fix collection code, and rename stream to match
- Fix parsing of directories full of files


[0.11.2][] - 2010-04-11
-----------------------

### Fixes
- Fix initrd sanity check to use the right proc path
- Don't return a bogus error value when dumping state
- Add -c to aid manual console debugging


[0.11.1][] - 2010-03-28
-----------------------

### Changes
- Even simpler initrd setup: create a single directory: /lib/bootchart/tmpfs


[0.11][] - 2010-03-21
---------------------

### Changes
- **bootchartd:** Far simpler, less shell, more robustness
- **collector:** Remove the -p argument - we always mount proc
- **collector:** Requires /lib/bootchart (make install-chroot) to be present (also in the initrd) with a kmsg node included
- **collector:** Add a --probe-running mode
- Ptrace re-write gives much better early-boot-time resolution
- Unconditional chroot /lib/bootchart/chroot - we mount proc there ourselves
- Log extraction requires no common file-system view


[0.10.1][] - 2009-11-15
-----------------------

### Changes
- Split collector install in Makefile, by Kel Modderman

### Fixes
- Collector arg -m should mount /proc, by Kel Modderman
- Remove bogus vcsid code, by Kel Modderman
- Remove bogus debug code, by Kel Modderman
- Accept process names containing spaces, by Kel Modderman


[0.10.0][] - 2009-11-08
-----------------------

### Changes
- **interactive UI:** Much faster rendering by manual clipping, by Michael
- **interactive UI:** Horizontal scaling, by Michael
- **interactive UI:** Remove annoying page-up/down bindings, by Michael
- **initrd:** Port to Mandriva, by Federic Crozat
- **initrd:** Improved process waiting, by Federic Crozat
- **initrd:** Improved initrd detection / jail tagging, by Federic Crozat
- Implement a built-in usleep to help initrd deps, by Michael

### Fixes
- **rendering:** Fix for unknown exceptions, by Anders Norgaard
- **initrd:** Inittab commenting fix, by Federic Crozat
- **initrd:** Fix for un-detectable accton behaviour change, by Federic Crozat


[0.0.9][] - 2009-09-06
----------------------

### Fixes
- Fix initrd bug


[0.0.8][] - 2009-09-05
----------------------

### Changes
- Add a filename string to the window title in interactive mode
- Add a NEWS file


[bootchart2]:    https://github.com/xrmx/bootchart
[UNRELEASED]:    https://github.com/finit-project/InitViz/compare/v0.14.9...HEAD
[0.14.9]:        https://github.com/xrmx/bootchart/releases/tag/0.14.9
[0.14.8]:        https://github.com/xrmx/bootchart/releases/tag/0.14.8
[0.14.7]:        https://github.com/xrmx/bootchart/releases/tag/0.14.7
[0.14.6]:        https://github.com/xrmx/bootchart/releases/tag/0.14.6
[0.14.5]:        https://github.com/xrmx/bootchart/releases/tag/0.14.5
[0.14.4]:        https://github.com/xrmx/bootchart/releases/tag/0.14.4
[0.14.2]:        https://github.com/xrmx/bootchart/releases/tag/0.14.2
[0.14.1]:        https://github.com/xrmx/bootchart/releases/tag/0.14.1
[0.14.0]:        https://github.com/xrmx/bootchart/releases/tag/0.14.0
[0.12.6]:        https://github.com/xrmx/bootchart/releases/tag/0.12.6
[0.12.5]:        https://github.com/xrmx/bootchart/releases/tag/0.12.5
[0.12.4]:        https://github.com/xrmx/bootchart/releases/tag/0.12.4
[0.12.3]:        https://github.com/xrmx/bootchart/releases/tag/0.12.3
[0.12.2]:        https://github.com/xrmx/bootchart/releases/tag/0.12.2
[0.12.1]:        https://github.com/xrmx/bootchart/releases/tag/0.12.1
[0.12.0]:        https://github.com/xrmx/bootchart/releases/tag/0.12.0
[0.11.4]:        https://github.com/xrmx/bootchart/releases/tag/0.11.4
[0.11.3]:        https://github.com/xrmx/bootchart/releases/tag/0.11.3
[0.11.2]:        https://github.com/xrmx/bootchart/releases/tag/0.11.2
[0.11.1]:        https://github.com/xrmx/bootchart/releases/tag/0.11.1
[0.11]:          https://github.com/xrmx/bootchart/releases/tag/0.11
[0.10.1]:        https://github.com/xrmx/bootchart/releases/tag/0.10.1
[0.10.0]:        https://github.com/xrmx/bootchart/releases/tag/0.10.0
[0.0.9]:         https://github.com/xrmx/bootchart/releases/tag/0.0.9
[0.0.8]:         https://github.com/xrmx/bootchart/releases/tag/0.0.8
