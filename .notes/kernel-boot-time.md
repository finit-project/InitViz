● Perfect! I've completed my investigation. Here's what I found:

  Kernel Boot Time Visualization - Already Implemented! ✓

  The feature you're looking for already exists in this codebase. Here's how it works:

  1. Collector Support (collector/dump.c:338-384)

  - Function dump_dmsg() extracts kernel dmesg log using klogctl()
  - Called automatically when !args.relative_time (collector.c:862)
  - Writes kernel log to a file called dmesg

  2. Parsing Support (pybootchartgui/parsing.py:523)

  - Function _parse_dmesg() parses kernel boot messages
  - Creates a "k-boot" process starting at time 0.1
  - Parses kernel initcalls like calling migration_init+0x0/0x6b @ 1
  - Sets kernel duration when seeing "Write protecting" or "Freeing unused kernel memory" messages

  3. Visualization Support (pybootchartgui/gui.py:495-502)

  - Creates a separate "Kernel boot" tab in the GUI
  - Only appears when trace.kernel exists and has >2 processes
  - Shows the kernel initialization process tree before userspace starts

  The Issue

  Your /tmp/bootlog.tgz was captured by BusyBox bootchartd (as shown in the header: init=/sbin/bootchartd), which doesn't dump dmesg. That's why it only contains:
  - header
  - proc_diskstats.log
  - proc_ps.log
  - proc_stat.log

  Missing: dmesg file

  The Solution

  To see kernel boot time visualization, you need to use this project's bootchartd collector instead of BusyBox bootchartd. This project's collector will automatically dump dmesg (unless using -r relative time flag), and the GUI will show a "Kernel boot" tab with the kernel initialization timeline.

  The feature works exactly like systemd-analyze - it shows kernel initcalls, their timing, and the kernel boot process before init starts!
