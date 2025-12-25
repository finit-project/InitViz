#  This file is part of pybootchartgui.

#  pybootchartgui is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  pybootchartgui is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with pybootchartgui. If not, see <http://www.gnu.org/licenses/>.

import signal
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk as gtk
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject as gobject
from gi.repository import GObject

from . import draw
from .draw import RenderOptions

class PyBootchartWidget(gtk.DrawingArea, gtk.Scrollable):
    __gsignals__ = {
            'clicked' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING, Gdk.Event)),
            'position-changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_INT)),
            'set-scroll-adjustments' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gtk.Adjustment, gtk.Adjustment))
    }

    hadjustment = GObject.property(type=Gtk.Adjustment,
                                   default=Gtk.Adjustment(),
                                   flags=GObject.PARAM_READWRITE)
    hscroll_policy = GObject.property(type=Gtk.ScrollablePolicy,
                                      default=Gtk.ScrollablePolicy.MINIMUM,
                                      flags=GObject.PARAM_READWRITE)
    vadjustment = GObject.property(type=Gtk.Adjustment,
                                   default=Gtk.Adjustment(),
                                   flags=GObject.PARAM_READWRITE)
    vscroll_policy = GObject.property(type=Gtk.ScrollablePolicy,
                                      default=Gtk.ScrollablePolicy.MINIMUM,
                                      flags=GObject.PARAM_READWRITE)

    def __init__(self, trace, options, xscale):
        gtk.DrawingArea.__init__(self)

        self.trace = trace
        self.options = options

        self.set_can_focus(True)

        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.connect("button-press-event", self.on_area_button_press)
        self.connect("button-release-event", self.on_area_button_release)
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.POINTER_MOTION_HINT_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.connect("motion-notify-event", self.on_area_motion_notify)
        self.add_events(Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.SMOOTH_SCROLL_MASK)
        self.connect("scroll-event", self.on_area_scroll_event)
        self.connect('key-press-event', self.on_key_press_event)

        self.connect("size-allocate", self.on_allocation_size_changed)
        self.connect("position-changed", self.on_position_changed)

        self.connect("draw", self.on_draw)

        self.zoom_ratio = 1.0
        self.xscale = xscale
        self.x, self.y = 0.0, 0.0

        self.chart_width, self.chart_height = draw.extents(self.options, self.xscale, self.trace)
        self.our_width, self.our_height = self.chart_width, self.chart_height

        # Use the GObject properties for adjustments to work with Scrollable
        self.hadj = self.get_hadjustment()
        if not self.hadj:
            self.hadj = gtk.Adjustment(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
            self.set_hadjustment(self.hadj)
        self.vadj = self.get_vadjustment()
        if not self.vadj:
            self.vadj = gtk.Adjustment(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
            self.set_vadjustment(self.vadj)
        self.vadj.connect('value-changed', self.on_adjustments_changed)
        self.hadj.connect('value-changed', self.on_adjustments_changed)

    def bound_vals(self):
        # Bound x and y to valid scroll positions
        # self.x, self.y are in chart coordinates
        # our_width, our_height are in screen pixels, so convert to chart coords
        self.x = max(0, self.x)
        self.y = max(0, self.y)
        max_x = self.chart_width - self.our_width / self.zoom_ratio
        max_y = self.chart_height - self.our_height / self.zoom_ratio
        self.x = min(max(0, max_x), self.x)
        self.y = min(max(0, max_y), self.y)

    def on_draw(self, darea, cr):
        # set a clip region
        #cr.rectangle(
        #        self.x, self.y,
        #        self.chart_width, self.chart_height
        #)
        #cr.clip()
        cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
        cr.paint()
        cr.scale(self.zoom_ratio, self.zoom_ratio)
        cr.translate(-self.x, -self.y)
        draw.render(cr, self.options, self.xscale, self.trace)

    def position_changed(self):
        self.emit("position-changed", self.x, self.y)

    ZOOM_INCREMENT = 1.25

    def zoom_image (self, zoom_ratio):
        self.zoom_ratio = zoom_ratio
        self._set_scroll_adjustments()
        self.queue_draw()

    def zoom_to_rect (self, rect):
        zoom_ratio = float(rect.width)/float(self.chart_width)
        self.zoom_image(zoom_ratio)
        self.x = 0
        self.position_changed()

    def set_xscale(self, xscale):
        old_mid_x = self.x + self.hadj.get_page_size() / 2
        self.xscale = xscale
        self.chart_width, self.chart_height = draw.extents(self.options, self.xscale, self.trace)
        new_x = old_mid_x
        self.zoom_image (self.zoom_ratio)

    def on_expand(self, action):
        self.set_xscale (self.xscale * 1.5)

    def on_contract(self, action):
        self.set_xscale (self.xscale / 1.5)

    def on_zoom_in(self, action):
        self.zoom_image(self.zoom_ratio * self.ZOOM_INCREMENT)

    def on_zoom_out(self, action):
        self.zoom_image(self.zoom_ratio / self.ZOOM_INCREMENT)

    def on_zoom_fit(self, action):
        self.zoom_to_rect(self.get_allocation())

    def on_zoom_100(self, action):
        self.zoom_image(1.0)
        self.set_xscale(1.0)

    POS_INCREMENT = 100

    def on_key_press_event(self, widget, event):
        if event.keyval == Gdk.keyval_from_name("Left"):
            self.x -= self.POS_INCREMENT/self.zoom_ratio
        elif event.keyval == Gdk.keyval_from_name("Right"):
            self.x += self.POS_INCREMENT/self.zoom_ratio
        elif event.keyval == Gdk.keyval_from_name("Up"):
            self.y -= self.POS_INCREMENT/self.zoom_ratio
        elif event.keyval == Gdk.keyval_from_name("Down"):
            self.y += self.POS_INCREMENT/self.zoom_ratio
        else:
            return False
        self.bound_vals()
        self.queue_draw()
        self.position_changed()
        return True

    def on_area_button_press(self, area, event):
        if event.button == 2 or event.button == 1:
            window = self.get_window()
            window.set_cursor(Gdk.Cursor(Gdk.CursorType.FLEUR))
            self.prevmousex = event.x
            self.prevmousey = event.y
        if event.type not in (Gdk.EventType.BUTTON_PRESS, Gdk.EventType.BUTTON_RELEASE):
            return False
        return False

    def on_area_button_release(self, area, event):
        if event.button == 2 or event.button == 1:
            window = self.get_window()
            window.set_cursor(Gdk.Cursor(Gdk.CursorType.ARROW))
            self.prevmousex = None
            self.prevmousey = None
            return True
        return False

    def on_area_scroll_event(self, area, event):
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            # Handle both discrete and smooth scrolling for zoom
            if event.direction == Gdk.ScrollDirection.UP:
                self.zoom_image(self.zoom_ratio * self.ZOOM_INCREMENT)
                return True
            elif event.direction == Gdk.ScrollDirection.DOWN:
                self.zoom_image(self.zoom_ratio / self.ZOOM_INCREMENT)
                return True
            elif event.direction == Gdk.ScrollDirection.SMOOTH:
                # For smooth scrolling, check the deltas
                success, delta_x, delta_y = event.get_scroll_deltas()
                if success and delta_y != 0:
                    if delta_y < 0:
                        self.zoom_image(self.zoom_ratio * self.ZOOM_INCREMENT)
                    else:
                        self.zoom_image(self.zoom_ratio / self.ZOOM_INCREMENT)
                    return True
        else:
            # Handle regular scrolling by adjusting the scrollbar values
            if event.direction == Gdk.ScrollDirection.UP:
                self.vadj.set_value(max(self.vadj.get_lower(),
                                       self.vadj.get_value() - self.vadj.get_step_increment()))
                return True
            elif event.direction == Gdk.ScrollDirection.DOWN:
                self.vadj.set_value(min(self.vadj.get_upper() - self.vadj.get_page_size(),
                                       self.vadj.get_value() + self.vadj.get_step_increment()))
                return True
            elif event.direction == Gdk.ScrollDirection.SMOOTH:
                # For smooth scrolling, adjust based on deltas
                success, delta_x, delta_y = event.get_scroll_deltas()
                if success:
                    if delta_y != 0:
                        # Vertical scroll
                        new_val = self.vadj.get_value() + delta_y * self.vadj.get_step_increment()
                        new_val = max(self.vadj.get_lower(),
                                     min(self.vadj.get_upper() - self.vadj.get_page_size(), new_val))
                        self.vadj.set_value(new_val)
                    if delta_x != 0:
                        # Horizontal scroll
                        new_val = self.hadj.get_value() + delta_x * self.hadj.get_step_increment()
                        new_val = max(self.hadj.get_lower(),
                                     min(self.hadj.get_upper() - self.hadj.get_page_size(), new_val))
                        self.hadj.set_value(new_val)
                    return True
        return False

    def on_area_motion_notify(self, area, event):
        state = event.state
        if state & Gdk.ModifierType.BUTTON2_MASK or state & Gdk.ModifierType.BUTTON1_MASK:
            x, y = int(event.x), int(event.y)
            # pan the image
            self.x += (self.prevmousex - x)/self.zoom_ratio
            self.y += (self.prevmousey - y)/self.zoom_ratio
            self.bound_vals()
            self.queue_draw()
            self.prevmousex = x
            self.prevmousey = y
            self.position_changed()
        return True

    def on_allocation_size_changed(self, widget, allocation):
        if allocation.width > 0 and allocation.height > 0:
            # Check if size actually changed to avoid unnecessary updates
            if self.our_width == allocation.width and self.our_height == allocation.height:
                return

            self.our_width = allocation.width
            self.our_height = allocation.height

            # In GTK adjustments:
            # - upper = total content size
            # - page_size = visible window size
            # - value can range from 0 to (upper - page_size)
            h_upper = self.zoom_ratio * self.chart_width
            v_upper = self.zoom_ratio * self.chart_height

            # Clamp current values to new valid range [0, upper - page_size]
            h_value = max(0.0, min(self.hadj.get_value(), h_upper - allocation.width))
            v_value = max(0.0, min(self.vadj.get_value(), v_upper - allocation.height))

            # Block the value-changed signal while we update to prevent feedback loops
            self.vadj.handler_block_by_func(self.on_adjustments_changed)
            self.hadj.handler_block_by_func(self.on_adjustments_changed)

            # Use configure() to set all adjustment values at once in GTK3
            self.hadj.configure(
                value=h_value,
                lower=0.0,
                upper=h_upper,
                step_increment=allocation.width * 0.1,
                page_increment=allocation.width * 0.9,
                page_size=allocation.width
            )
            self.vadj.configure(
                value=v_value,
                lower=0.0,
                upper=v_upper,
                step_increment=allocation.height * 0.1,
                page_increment=allocation.height * 0.9,
                page_size=allocation.height
            )

            # Unblock and manually sync self.x/self.y
            self.hadj.handler_unblock_by_func(self.on_adjustments_changed)
            self.vadj.handler_unblock_by_func(self.on_adjustments_changed)

            # Manually update our position to match the adjustments
            self.x = h_value / self.zoom_ratio
            self.y = v_value / self.zoom_ratio

            self.queue_draw()

    def _set_scroll_adjustments(self):
        # Update upper bounds when zooming
        h_upper = self.zoom_ratio * self.chart_width
        v_upper = self.zoom_ratio * self.chart_height

        # Get current page sizes
        h_page = self.hadj.get_page_size()
        v_page = self.vadj.get_page_size()

        # Clamp current values to new valid range [0, upper - page_size]
        h_value = max(0.0, min(self.hadj.get_value(), h_upper - h_page))
        v_value = max(0.0, min(self.vadj.get_value(), v_upper - v_page))

        # Use configure() to update all values atomically
        self.hadj.configure(
            value=h_value,
            lower=0.0,
            upper=h_upper,
            step_increment=self.hadj.get_step_increment(),
            page_increment=self.hadj.get_page_increment(),
            page_size=h_page
        )
        self.vadj.configure(
            value=v_value,
            lower=0.0,
            upper=v_upper,
            step_increment=self.vadj.get_step_increment(),
            page_increment=self.vadj.get_page_increment(),
            page_size=v_page
        )

    def on_adjustments_changed(self, adj):
        self.x = self.hadj.get_value() / self.zoom_ratio
        self.y = self.vadj.get_value() / self.zoom_ratio
        self.queue_draw()

    def on_position_changed(self, widget, x, y):
        self.hadj.set_value(x * self.zoom_ratio)
        #self.hadj.value_changed()
        self.vadj.set_value(y * self.zoom_ratio)

class PyBootchartShell(gtk.VBox):
    ui = '''
    <ui>
            <toolbar name="ToolBar">
                    <toolitem action="Expand"/>
                    <toolitem action="Contract"/>
                    <separator/>
                    <toolitem action="ZoomIn"/>
                    <toolitem action="ZoomOut"/>
                    <toolitem action="ZoomFit"/>
                    <toolitem action="Zoom100"/>
            </toolbar>
    </ui>
    '''
    def __init__(self, window, trace, options, xscale):
        gtk.VBox.__init__(self)

        self.window = window
        self.trace = trace
        self.widget2 = PyBootchartWidget(trace, options, xscale)

        uimanager = self.uimanager = gtk.UIManager()
        accelgroup = uimanager.get_accel_group()
        window.add_accel_group(accelgroup)

        actiongroup = gtk.ActionGroup('Actions')
        self.actiongroup = actiongroup
        actiongroup.add_actions((
                ('Expand', gtk.STOCK_ADD, '_Expand Timeline', None, 'Expand timeline', self.widget2.on_expand),
                ('Contract', gtk.STOCK_REMOVE, '_Contract Timeline', None, 'Contract timeline', self.widget2.on_contract),
                ('ZoomIn', gtk.STOCK_ZOOM_IN, None, None, 'Zoom in', self.widget2.on_zoom_in),
                ('ZoomOut', gtk.STOCK_ZOOM_OUT, None, None, 'Zoom out', self.widget2.on_zoom_out),
                ('ZoomFit', gtk.STOCK_ZOOM_FIT, 'Fit Width', None, 'Fit to width', self.widget2.on_zoom_fit),
                ('Zoom100', gtk.STOCK_ZOOM_100, None, None, 'Original size', self.widget2.on_zoom_100),
        ))

        uimanager.insert_action_group(actiongroup, 0)
        uimanager.add_ui_from_string(self.ui)

        # Scrolled window
        scrolled = gtk.ScrolledWindow(self.widget2.hadj, self.widget2.vadj)
        scrolled.add(self.widget2)
        scrolled.set_policy(gtk.PolicyType.ALWAYS, gtk.PolicyType.ALWAYS)

        # Get toolbar from UIManager
        toolbar = uimanager.get_widget('/ToolBar')

        # Pack widgets: toolbar, scrolled area
        self.pack_start(toolbar, False, True, 0)
        self.pack_start(scrolled, True, True, 0)
        self.show_all()

    def grab_focus(self, window):
        window.set_focus(self.widget2)

    def on_toggle_show_pid(self, action):
        self.widget2.options.app_options.show_pid = action.get_active()
        self.widget2.chart_width, self.widget2.chart_height = draw.extents(self.widget2.options, self.widget2.xscale, self.trace)
        self.widget2._set_scroll_adjustments()
        self.widget2.queue_draw()

    def on_toggle_show_all(self, action):
        self.widget2.options.app_options.show_all = action.get_active()
        self.widget2.chart_width, self.widget2.chart_height = draw.extents(self.widget2.options, self.widget2.xscale, self.trace)
        self.widget2._set_scroll_adjustments()
        self.widget2.queue_draw()


class PyBootchartWindow(gtk.Window):

    def __init__(self, trace, app_options):
        gtk.Window.__init__(self)

        window = self
        window.set_title("Bootchart %s" % trace.filename)
        window.set_default_size(750, 550)

        self.trace = trace
        self.app_options = app_options

        # Create main VBox to hold menubar and tabs
        main_vbox = gtk.VBox(False, 0)
        window.add(main_vbox)

        # Create menu bar
        uimanager = gtk.UIManager()
        accelgroup = uimanager.get_accel_group()
        window.add_accel_group(accelgroup)

        actiongroup = gtk.ActionGroup('MenuActions')
        actiongroup.add_actions((
                ('File', None, '_File'),
                ('Open', gtk.STOCK_OPEN, None, '<Control>O', 'Open bootchart', self.on_open),
                ('Save', gtk.STOCK_SAVE_AS, None, '<Control>S', 'Save bootchart', self.on_save),
                ('Close', gtk.STOCK_CLOSE, None, '<Control>W', 'Close window', self.on_close),
                ('View', None, '_View'),
                ('Expand', gtk.STOCK_ADD, '_Expand Timeline', 'plus', 'Expand timeline', self.on_expand),
                ('Contract', gtk.STOCK_REMOVE, '_Contract Timeline', 'minus', 'Contract timeline', self.on_contract),
                ('ZoomIn', gtk.STOCK_ZOOM_IN, None, '<Control>plus', 'Zoom in', self.on_zoom_in),
                ('ZoomOut', gtk.STOCK_ZOOM_OUT, None, '<Control>minus', 'Zoom out', self.on_zoom_out),
                ('ZoomFit', gtk.STOCK_ZOOM_FIT, 'Fit Width', None, 'Fit to width', self.on_zoom_fit),
                ('Zoom100', gtk.STOCK_ZOOM_100, None, '<Control>0', 'Original size', self.on_zoom_100),
        ))

        actiongroup.add_toggle_actions((
                ('ShowPID', None, 'Show _PID', None, 'Show process IDs', self.on_toggle_show_pid, app_options.show_pid),
                ('ShowAll', None, 'Show _All', None, 'Show full command lines and arguments', self.on_toggle_show_all, app_options.show_all),
        ))

        uimanager.insert_action_group(actiongroup, 0)

        menu_ui = '''
        <ui>
                <menubar name="MenuBar">
                        <menu action="File">
                                <menuitem action="Open"/>
                                <menuitem action="Save"/>
                                <separator/>
                                <menuitem action="Close"/>
                        </menu>
                        <menu action="View">
                                <menuitem action="Expand"/>
                                <menuitem action="Contract"/>
                                <separator/>
                                <menuitem action="ZoomIn"/>
                                <menuitem action="ZoomOut"/>
                                <menuitem action="ZoomFit"/>
                                <menuitem action="Zoom100"/>
                                <separator/>
                                <menuitem action="ShowPID"/>
                                <menuitem action="ShowAll"/>
                        </menu>
                </menubar>
        </ui>
        '''
        uimanager.add_ui_from_string(menu_ui)
        menubar = uimanager.get_widget('/MenuBar')
        main_vbox.pack_start(menubar, False, True, 0)

        # Create tab notebook
        tab_page = gtk.Notebook()
        self.tab_page = tab_page
        main_vbox.pack_start(tab_page, True, True, 0)

        full_opts = RenderOptions(app_options)
        full_tree = PyBootchartShell(window, trace, full_opts, 1.0)
        tab_page.append_page(full_tree, gtk.Label("Full tree"))
        self.tabs = [full_tree]

        if trace.kernel is not None and len(trace.kernel) > 2:
            kernel_opts = RenderOptions(app_options)
            kernel_opts.cumulative = False
            kernel_opts.charts = False
            kernel_opts.kernel_only = True
            kernel_tree = PyBootchartShell(window, trace, kernel_opts, 5.0)
            tab_page.append_page(kernel_tree, gtk.Label("Kernel boot"))
            self.tabs.append(kernel_tree)

        full_tree.grab_focus(self)

        # Add Ctrl+Q as additional keybinding for close
        self.connect('key-press-event', self.on_key_press)

        self.show_all()

    def on_key_press(self, widget, event):
        # Handle Ctrl+Q as alias for Ctrl+W (Close)
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            if event.keyval == Gdk.keyval_from_name('q') or event.keyval == Gdk.keyval_from_name('Q'):
                self.destroy()
                return True
        return False

    def get_current_tab(self):
        page_num = self.tab_page.get_current_page()
        return self.tabs[page_num]

    def on_expand(self, action):
        self.get_current_tab().widget2.on_expand(action)

    def on_contract(self, action):
        self.get_current_tab().widget2.on_contract(action)

    def on_zoom_in(self, action):
        self.get_current_tab().widget2.on_zoom_in(action)

    def on_zoom_out(self, action):
        self.get_current_tab().widget2.on_zoom_out(action)

    def on_zoom_fit(self, action):
        self.get_current_tab().widget2.on_zoom_fit(action)

    def on_zoom_100(self, action):
        self.get_current_tab().widget2.on_zoom_100(action)

    def on_open(self, action):
        dialog = gtk.FileChooserDialog(
            title="Open Bootchart",
            parent=self,
            action=gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            gtk.STOCK_CANCEL, gtk.ResponseType.CANCEL,
            gtk.STOCK_OPEN, gtk.ResponseType.OK
        )

        # Add file filters
        filter_tgz = gtk.FileFilter()
        filter_tgz.set_name("Bootchart files")
        filter_tgz.add_pattern("*.tgz")
        filter_tgz.add_pattern("*.tar.gz")
        dialog.add_filter(filter_tgz)

        filter_all = gtk.FileFilter()
        filter_all.set_name("All files")
        filter_all.add_pattern("*")
        dialog.add_filter(filter_all)

        response = dialog.run()
        if response == gtk.ResponseType.OK:
            filename = dialog.get_filename()
            dialog.destroy()
            # Reload the window with new file
            from . import parsing

            class Writer:
                def error(self, msg): print(msg)
                def warn(self, msg): print(msg)
                def info(self, msg): print(msg)
                def status(self, msg): print(msg)

            try:
                writer = Writer()
                trace = parsing.Trace(writer, [filename], self.app_options)
                self.destroy()
                win = PyBootchartWindow(trace, self.app_options)
                win.connect('destroy', gtk.main_quit)
                win.show()
            except Exception as e:
                error_dialog = gtk.MessageDialog(
                    parent=self,
                    flags=0,
                    message_type=gtk.MessageType.ERROR,
                    buttons=gtk.ButtonsType.OK,
                    text="Error opening file"
                )
                error_dialog.format_secondary_text(str(e))
                error_dialog.run()
                error_dialog.destroy()
        else:
            dialog.destroy()

    def on_save(self, action):
        dialog = gtk.FileChooserDialog(
            title="Save Bootchart",
            parent=self,
            action=gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            gtk.STOCK_CANCEL, gtk.ResponseType.CANCEL,
            gtk.STOCK_SAVE, gtk.ResponseType.OK
        )
        dialog.set_do_overwrite_confirmation(True)
        dialog.set_current_name("bootchart.svg")

        # Add file filters for different formats
        filter_svg = gtk.FileFilter()
        filter_svg.set_name("SVG (*.svg)")
        filter_svg.add_pattern("*.svg")
        filter_svg.ext = 'svg'
        dialog.add_filter(filter_svg)

        filter_png = gtk.FileFilter()
        filter_png.set_name("PNG (*.png)")
        filter_png.add_pattern("*.png")
        filter_png.ext = 'png'
        dialog.add_filter(filter_png)

        filter_pdf = gtk.FileFilter()
        filter_pdf.set_name("PDF (*.pdf)")
        filter_pdf.add_pattern("*.pdf")
        filter_pdf.ext = 'pdf'
        dialog.add_filter(filter_pdf)

        filter_all = gtk.FileFilter()
        filter_all.set_name("All files")
        filter_all.add_pattern("*")
        dialog.add_filter(filter_all)

        # Auto-update extension when filter changes
        def on_filter_changed(dialog, param):
            current_filter = dialog.get_filter()
            if current_filter and current_filter != filter_all:
                ext = getattr(current_filter, 'ext', None)
                if ext:
                    current_name = dialog.get_current_name()
                    if current_name:
                        # Strip existing extension and add new one
                        base_name = current_name.rsplit('.', 1)[0] if '.' in current_name else current_name
                        dialog.set_current_name(f"{base_name}.{ext}")

        dialog.connect('notify::filter', on_filter_changed)

        response = dialog.run()
        if response == gtk.ResponseType.OK:
            filename = dialog.get_filename()
            dialog.destroy()

            from . import batch
            class Writer:
                def error(self, msg): print(msg)
                def warn(self, msg): print(msg)
                def info(self, msg): print(msg)
                def status(self, msg): print(msg)

            try:
                writer = Writer()
                current_tab = self.get_current_tab()
                batch.render(writer, self.trace, current_tab.widget2.options, filename)
                info_dialog = gtk.MessageDialog(
                    parent=self,
                    flags=0,
                    message_type=gtk.MessageType.INFO,
                    buttons=gtk.ButtonsType.OK,
                    text="File saved successfully"
                )
                info_dialog.format_secondary_text(f"Saved to {filename}")
                info_dialog.run()
                info_dialog.destroy()
            except Exception as e:
                error_dialog = gtk.MessageDialog(
                    parent=self,
                    flags=0,
                    message_type=gtk.MessageType.ERROR,
                    buttons=gtk.ButtonsType.OK,
                    text="Error saving file"
                )
                error_dialog.format_secondary_text(str(e))
                error_dialog.run()
                error_dialog.destroy()
        else:
            dialog.destroy()

    def on_close(self, action):
        self.destroy()

    def on_toggle_show_pid(self, action):
        # Update all tabs (they will update app_options)
        for tab in self.tabs:
            tab.on_toggle_show_pid(action)

    def on_toggle_show_all(self, action):
        # Update all tabs (they will update app_options)
        for tab in self.tabs:
            tab.on_toggle_show_all(action)


def show(trace, options):
    win = PyBootchartWindow(trace, options)
    win.connect('destroy', gtk.main_quit)

    def signal_handler(sig, _):
        print(f"\nReceived signal {sig}, closing...")
        win.destroy()

    signal.signal(signal.SIGINT, signal_handler)
    GObject.timeout_add(100, lambda: True)

    gtk.main()
