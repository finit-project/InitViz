#  This file is part of initviz.

#  initviz is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  initviz is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with initviz. If not, see <http://www.gnu.org/licenses/>.

import signal
import math
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk as gtk
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject as gobject
from gi.repository import GObject

from . import draw
from .draw import RenderOptions
from . import get_version

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
        self.best_fit_mode = True  # Enable best fit by default
        self.prevmousex = None
        self.prevmousey = None

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
    WHEEL_ZOOM_INCREMENT = 1.1  # Smaller increment for mouse wheel zoom

    def zoom_image(self, zoom_ratio, auto_fit=False):
        """Zoom the image. If auto_fit is False, disable best_fit_mode."""
        if not auto_fit and self.best_fit_mode:
            self.best_fit_mode = False
            # Update the menu checkbox
            if hasattr(self, 'parent_window') and self.parent_window:
                self.parent_window.update_best_fit_action(False)
        self.zoom_ratio = zoom_ratio
        self._set_scroll_adjustments()
        self.queue_draw()

    def zoom_to_rect (self, rect):
        zoom_ratio = float(rect.width)/float(self.chart_width)
        self.zoom_image(zoom_ratio)
        self.x = 0
        self.position_changed()

    def zoom_to_best_fit(self, rect):
        """Zoom to best fit - fits width for readability, allows vertical scrolling"""
        if rect.width <= 0 or rect.height <= 0:
            return

        # Only fit to width - bootcharts are vertical documents meant to be scrolled
        # Fitting to height makes text unreadable
        # The default xscale of 3.0 provides enough width for headers and labels
        zoom_ratio = float(rect.width) / float(self.chart_width)

        # Apply the zoom
        self.zoom_image(zoom_ratio, auto_fit=True)

        # Reset to top-left (but horizontal scrolling will be available if content is wider)
        self.x = 0
        self.y = 0
        self.position_changed()

    def set_xscale(self, xscale):
        old_mid_x = self.x + self.hadj.get_page_size() / 2
        self.xscale = xscale
        self.chart_width, self.chart_height = draw.extents(self.options, self.xscale, self.trace)
        new_x = old_mid_x
        # Don't disable best fit for timeline expansion/contraction
        was_best_fit = self.best_fit_mode
        self.zoom_image(self.zoom_ratio)
        self.best_fit_mode = was_best_fit
        # If best fit is enabled, re-apply it with new chart dimensions
        if self.best_fit_mode:
            allocation = self.get_allocation()
            self.zoom_to_best_fit(allocation)

    def on_expand(self, action):
        self.set_xscale (self.xscale * 1.5)

    def on_contract(self, action):
        self.set_xscale (self.xscale / 1.5)

    def on_zoom_in(self, action):
        self.zoom_image(self.zoom_ratio * self.ZOOM_INCREMENT)

    def on_zoom_out(self, action):
        self.zoom_image(self.zoom_ratio / self.ZOOM_INCREMENT)

    def on_zoom_fit(self, action):
        if self.best_fit_mode:
            self.best_fit_mode = False  # Disable best fit when manually fitting
            # Update the menu checkbox
            if hasattr(self, 'parent_window') and self.parent_window:
                self.parent_window.update_best_fit_action(False)
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
            # Use smaller increment for mouse wheel to reduce sensitivity
            if event.direction == Gdk.ScrollDirection.UP:
                self.zoom_image(self.zoom_ratio * self.WHEEL_ZOOM_INCREMENT)
                return True
            elif event.direction == Gdk.ScrollDirection.DOWN:
                self.zoom_image(self.zoom_ratio / self.WHEEL_ZOOM_INCREMENT)
                return True
            elif event.direction == Gdk.ScrollDirection.SMOOTH:
                # For smooth scrolling, check the deltas
                success, delta_x, delta_y = event.get_scroll_deltas()
                if success and delta_y != 0:
                    if delta_y < 0:
                        self.zoom_image(self.zoom_ratio * self.WHEEL_ZOOM_INCREMENT)
                    else:
                        self.zoom_image(self.zoom_ratio / self.WHEEL_ZOOM_INCREMENT)
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
            # Only pan if we have previous mouse positions
            if self.prevmousex is None or self.prevmousey is None:
                return True
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

            # If best fit mode is enabled, auto-fit on resize
            if self.best_fit_mode:
                self.zoom_to_best_fit(allocation)
                # Don't return - still need to configure adjustments below

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
    def __init__(self, window, trace, options, xscale):
        gtk.VBox.__init__(self)

        self.window = window
        self.trace = trace
        self.widget2 = PyBootchartWidget(trace, options, xscale)
        self.widget2.parent_window = window  # Store window reference for updating actions

        # Create search bar (initially hidden)
        self.search_bar = gtk.HBox(False, 6)
        self.search_bar.set_border_width(3)

        search_label = gtk.Label("Find:")
        self.search_bar.pack_start(search_label, False, False, 0)

        self.search_entry = gtk.Entry()
        self.search_entry.connect('changed', self.on_search_changed)
        self.search_entry.connect('key-press-event', self.on_search_key_press)
        self.search_bar.pack_start(self.search_entry, True, True, 0)

        # Previous button
        self.prev_button = gtk.Button()
        self.prev_button.set_relief(gtk.ReliefStyle.NONE)
        self.prev_button.add(gtk.Image.new_from_stock(gtk.STOCK_GO_UP, gtk.IconSize.MENU))
        self.prev_button.set_tooltip_text("Previous match")
        self.prev_button.connect('clicked', self.on_search_prev)
        self.search_bar.pack_start(self.prev_button, False, False, 0)

        # Next button
        self.next_button = gtk.Button()
        self.next_button.set_relief(gtk.ReliefStyle.NONE)
        self.next_button.add(gtk.Image.new_from_stock(gtk.STOCK_GO_DOWN, gtk.IconSize.MENU))
        self.next_button.set_tooltip_text("Next match")
        self.next_button.connect('clicked', self.on_search_next)
        self.search_bar.pack_start(self.next_button, False, False, 0)

        self.search_label = gtk.Label("")
        self.search_bar.pack_start(self.search_label, False, False, 0)

        close_button = gtk.Button()
        close_button.set_relief(gtk.ReliefStyle.NONE)
        close_button.add(gtk.Image.new_from_stock(gtk.STOCK_CLOSE, gtk.IconSize.MENU))
        close_button.connect('clicked', self.on_search_close)
        self.search_bar.pack_start(close_button, False, False, 0)

        # Track current match position
        self.search_matches = []  # List of (y_position, process) tuples
        self.current_match_index = 0

        self.pack_start(self.search_bar, False, False, 0)

        # Scrolled window
        scrolled = gtk.ScrolledWindow(self.widget2.hadj, self.widget2.vadj)
        scrolled.add(self.widget2)
        scrolled.set_policy(gtk.PolicyType.ALWAYS, gtk.PolicyType.ALWAYS)

        # Pack scrolled area only (toolbar is now in PyBootchartWindow)
        self.pack_start(scrolled, True, True, 0)
        self.show_all()
        self.search_bar.set_no_show_all(True)
        self.search_bar.hide()  # Ensure it's hidden by default

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

    def on_toggle_best_fit(self, action):
        self.widget2.best_fit_mode = action.get_active()
        if self.widget2.best_fit_mode:
            # Immediately apply best fit when enabled
            allocation = self.widget2.get_allocation()
            self.widget2.zoom_to_best_fit(allocation)

    def show_search(self):
        """Show the search bar and focus the entry"""
        self.search_bar.show()
        self.search_entry.grab_focus()

    def on_search_changed(self, entry):
        """Handle search text changes"""
        search_text = entry.get_text().lower()
        self.widget2.options.search_query = search_text if search_text else None

        # Build list of all matches and scroll to first
        if search_text:
            self.build_match_list(search_text)
            num_matches = len(self.search_matches)
            if num_matches > 0:
                self.current_match_index = 0
                self.update_match_label()
                self.scroll_to_match(self.current_match_index)
                # Enable/disable navigation buttons
                self.prev_button.set_sensitive(num_matches > 1)
                self.next_button.set_sensitive(num_matches > 1)
            else:
                self.search_label.set_text("0 matches")
                self.prev_button.set_sensitive(False)
                self.next_button.set_sensitive(False)
        else:
            self.search_label.set_text("")
            self.search_matches = []
            self.current_match_index = 0
            self.prev_button.set_sensitive(False)
            self.next_button.set_sensitive(False)

        # Redraw to highlight matches
        self.widget2.queue_draw()

    def count_matches(self, search_text):
        """Count how many processes match the search query"""
        count = 0
        proc_tree = self.widget2.options.proc_tree(self.trace)
        if proc_tree and proc_tree.process_tree:
            count = self._count_matches_recursive(proc_tree.process_tree, search_text)
        return count

    def _count_matches_recursive(self, process_list, search_text):
        """Recursively count matches in process tree"""
        count = 0
        for proc in process_list:
            # Check if process matches
            if search_text in proc.cmd.lower():
                count += 1
            elif proc.exe and search_text in proc.exe.lower():
                count += 1
            elif proc.args:
                for arg in proc.args:
                    if search_text in arg.lower():
                        count += 1
                        break
            # Check children
            if proc.child_list:
                count += self._count_matches_recursive(proc.child_list, search_text)
        return count

    def scroll_to_first_match(self, search_text):
        """Scroll viewport to show the first matching process"""
        proc_tree = self.widget2.options.proc_tree(self.trace)
        if not proc_tree or not proc_tree.process_tree:
            return

        # Constants from draw.py
        proc_h = 16  # Height of each process bar

        # Estimate starting Y position for processes
        # This needs to account for: header + charts (if shown) + process chart header
        # Rough estimates: header ~= 60-80px, charts (if enabled) ~= 200-300px
        # Process chart header = 60px
        if self.widget2.options.charts:
            # With charts enabled (default)
            start_y = 350  # Approximate: header + CPU chart + disk chart + mem chart + proc header
        else:
            # Charts disabled
            start_y = 120  # Approximate: header + proc header

        # Find Y position of first match (in chart coordinates)
        y_pos = self._find_first_match_position(proc_tree.process_tree, search_text, start_y, proc_h, proc_tree)

        if y_pos is not None:
            # Convert from chart coordinates to screen coordinates
            zoom_ratio = self.widget2.zoom_ratio
            y_screen = y_pos * zoom_ratio

            # Scroll to position, centering it in the viewport if possible
            vadj = self.widget2.vadj
            viewport_height = vadj.get_page_size()

            # Center the match in the viewport
            scroll_pos = y_screen - (viewport_height / 2)

            # Clamp to valid range
            scroll_pos = max(0, min(scroll_pos, vadj.get_upper() - viewport_height))

            vadj.set_value(scroll_pos)

    def _find_first_match_position(self, process_list, search_text, current_y, proc_h, proc_tree):
        """Recursively find Y position of first matching process"""
        for proc in process_list:
            # Check if this process matches
            if search_text in proc.cmd.lower():
                return current_y
            elif proc.exe and search_text in proc.exe.lower():
                return current_y
            elif proc.args:
                for arg in proc.args:
                    if search_text in arg.lower():
                        return current_y

            # Check children
            if proc.child_list:
                child_y = current_y + proc_h
                result = self._find_first_match_position(proc.child_list, search_text, child_y, proc_h, proc_tree)
                if result is not None:
                    return result

            # Move to next sibling
            current_y += proc_h * proc_tree.num_nodes([proc])

        return None

    def build_match_list(self, search_text):
        """Build a list of all matching processes with their Y positions"""
        self.search_matches = []
        proc_tree = self.widget2.options.proc_tree(self.trace)
        if not proc_tree or not proc_tree.process_tree:
            return

        # Constants from draw.py
        proc_h = 16

        # Estimate starting Y position
        if self.widget2.options.charts:
            start_y = 350
        else:
            start_y = 120

        # Collect all matches
        self._collect_matches_recursive(proc_tree.process_tree, search_text, start_y, proc_h, proc_tree)

    def _collect_matches_recursive(self, process_list, search_text, current_y, proc_h, proc_tree):
        """Recursively collect all matching processes"""
        for proc in process_list:
            # Check if this process matches
            matches = False
            if search_text in proc.cmd.lower():
                matches = True
            elif proc.exe and search_text in proc.exe.lower():
                matches = True
            elif proc.args:
                for arg in proc.args:
                    if search_text in arg.lower():
                        matches = True
                        break

            if matches:
                self.search_matches.append(current_y)

            # Check children
            if proc.child_list:
                child_y = current_y + proc_h
                self._collect_matches_recursive(proc.child_list, search_text, child_y, proc_h, proc_tree)

            # Move to next sibling
            current_y += proc_h * proc_tree.num_nodes([proc])

    def scroll_to_match(self, match_index):
        """Scroll to show the match at the given index"""
        if match_index < 0 or match_index >= len(self.search_matches):
            return

        y_pos = self.search_matches[match_index]

        # Convert from chart coordinates to screen coordinates
        zoom_ratio = self.widget2.zoom_ratio
        y_screen = y_pos * zoom_ratio

        # Scroll to position, centering it in the viewport if possible
        vadj = self.widget2.vadj
        viewport_height = vadj.get_page_size()

        # Center the match in the viewport
        scroll_pos = y_screen - (viewport_height / 2)

        # Clamp to valid range
        scroll_pos = max(0, min(scroll_pos, vadj.get_upper() - viewport_height))

        vadj.set_value(scroll_pos)

    def update_match_label(self):
        """Update the match count label"""
        if len(self.search_matches) > 0:
            self.search_label.set_text("%d/%d" % (self.current_match_index + 1, len(self.search_matches)))
        else:
            self.search_label.set_text("0 matches")

    def on_search_prev(self, button):
        """Navigate to previous match"""
        if len(self.search_matches) == 0:
            return

        self.current_match_index = (self.current_match_index - 1) % len(self.search_matches)
        self.update_match_label()
        self.scroll_to_match(self.current_match_index)
        self.widget2.queue_draw()

    def on_search_next(self, button):
        """Navigate to next match"""
        if len(self.search_matches) == 0:
            return

        self.current_match_index = (self.current_match_index + 1) % len(self.search_matches)
        self.update_match_label()
        self.scroll_to_match(self.current_match_index)
        self.widget2.queue_draw()

    def on_search_key_press(self, entry, event):
        """Handle key presses in search entry"""
        if event.keyval == Gdk.keyval_from_name('Escape'):
            self.on_search_close(None)
            return True
        elif event.keyval == Gdk.keyval_from_name('F3'):
            if event.state & Gdk.ModifierType.SHIFT_MASK:
                # Shift+F3 = Previous
                self.on_search_prev(None)
            else:
                # F3 = Next
                self.on_search_next(None)
            return True
        elif event.keyval == Gdk.keyval_from_name('Return'):
            # Enter = Next match
            self.on_search_next(None)
            return True
        return False

    def on_search_close(self, button):
        """Close the search bar"""
        self.search_bar.hide()
        self.search_entry.set_text("")
        self.widget2.options.search_query = None
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
        self.uimanager = uimanager
        accelgroup = uimanager.get_accel_group()
        window.add_accel_group(accelgroup)

        actiongroup = gtk.ActionGroup('MenuActions')
        actiongroup.add_actions((
                ('File', None, '_File'),
                ('Open', gtk.STOCK_OPEN, None, '<Control>O', 'Open bootchart', self.on_open),
                ('Save', gtk.STOCK_SAVE_AS, None, '<Control>S', 'Save bootchart', self.on_save),
                ('Print', gtk.STOCK_PRINT, None, '<Control>P', 'Print bootchart', self.on_print),
                ('Close', gtk.STOCK_CLOSE, None, '<Control>W', 'Close window', self.on_close),
                ('View', None, '_View'),
                ('Expand', gtk.STOCK_ADD, '_Expand Timeline', 'plus', 'Expand timeline', self.on_expand),
                ('Contract', gtk.STOCK_REMOVE, '_Contract Timeline', 'minus', 'Contract timeline', self.on_contract),
                ('ZoomIn', gtk.STOCK_ZOOM_IN, None, '<Control>plus', 'Zoom in', self.on_zoom_in),
                ('ZoomOut', gtk.STOCK_ZOOM_OUT, None, '<Control>minus', 'Zoom out', self.on_zoom_out),
                ('ZoomFit', gtk.STOCK_ZOOM_FIT, 'Fit Width', None, 'Fit to width', self.on_zoom_fit),
                ('Zoom100', gtk.STOCK_ZOOM_100, None, '<Control>0', 'Original size', self.on_zoom_100),
                ('Find', gtk.STOCK_FIND, None, '<Control>f', 'Find process', self.on_find),
                ('Sort', None, '_Sort'),
                ('Help', None, '_Help'),
                ('About', gtk.STOCK_ABOUT, None, None, 'About InitViz', self.on_about),
        ))

        actiongroup.add_toggle_actions((
                ('BestFit', None, '_Best Fit', None, 'Automatically fit content to window', self.on_toggle_best_fit, True),
                ('ShowPID', None, 'Show P_ID', '<Control>i', 'Show process IDs', self.on_toggle_show_pid, app_options.show_pid),
                ('ShowAll', None, 'Show _All', '<Control>a', 'Show full command lines and arguments', self.on_toggle_show_all, app_options.show_all),
                ('NoPrune', None, '_Trim Procs', '<Control>t', 'Trim the process tree to remove short-lived and idle processes', self.on_toggle_prune_procs, app_options.prune),
                ('ShowKernel', None, 'Show _Kernel Threads', '<Control>k', 'Show or hide kernel threads in the process tree', self.on_toggle_show_kernel, app_options.show_kernel if hasattr(app_options, 'show_kernel') else True),
                ('ShowTabs', None, 'Show _Tabs', None, 'Show or hide tab bar', self.on_toggle_tabs, True),
                ('ShowToolbar', None, 'Show _Toolbar', None, 'Show or hide toolbar', self.on_toggle_toolbar, True),
                ('ShowStatusbar', None, 'Show _Statusbar', None, 'Show or hide status bar', self.on_toggle_statusbar, True),
        ))

        # Ensure app_options has proc_sort attribute with default
        if not hasattr(app_options, 'proc_sort'):
            app_options.proc_sort = 'pid'

        # Radio actions for sort options
        sort_map_reverse = {'pid': 0, 'start-time': 1, 'cpu-time': 2, 'end-time': 3}
        sort_default = sort_map_reverse.get(app_options.proc_sort, 0)
        actiongroup.add_radio_actions((
                ('SortPID', None, 'By _PID', None, 'Sort processes by PID', 0),
                ('SortStartTime', None, 'By _Start Time', None, 'Sort processes by start time (default)', 1),
                ('SortCPUTime', None, 'By _CPU Time', None, 'Sort processes by CPU usage', 2),
                ('SortEndTime', None, 'By _End Time', None, 'Sort processes by end time (finish time)', 3),
        ), sort_default, self.on_sort_changed)

        uimanager.insert_action_group(actiongroup, 0)

        menu_ui = '''
        <ui>
                <menubar name="MenuBar">
                        <menu action="File">
                                <menuitem action="Open"/>
                                <menuitem action="Save"/>
                                <menuitem action="Print"/>
                                <separator/>
                                <menuitem action="Close"/>
                        </menu>
                        <menu action="View">
                                <menuitem action="Expand"/>
                                <menuitem action="Contract"/>
                                <separator/>
                                <menuitem action="Find"/>
                                <separator/>
                                <menuitem action="ZoomIn"/>
                                <menuitem action="ZoomOut"/>
                                <menuitem action="ZoomFit"/>
                                <menuitem action="Zoom100"/>
                                <menuitem action="BestFit"/>
                                <separator/>
                                <menuitem action="ShowPID"/>
                                <menuitem action="ShowAll"/>
                                <menuitem action="NoPrune"/>
                                <menuitem action="ShowKernel"/>
                                <separator/>
                                <menuitem action="ShowTabs"/>
                                <menuitem action="ShowToolbar"/>
                                <menuitem action="ShowStatusbar"/>
                        </menu>
                        <menu action="Sort">
                                <menuitem action="SortPID"/>
                                <menuitem action="SortStartTime"/>
                                <menuitem action="SortEndTime"/>
                                <menuitem action="SortCPUTime"/>
                        </menu>
                        <menu action="Help">
                                <menuitem action="About"/>
                        </menu>
                </menubar>
                <toolbar name="ToolBar">
                        <toolitem action="Open"/>
                        <toolitem action="Save"/>
                        <separator/>
                        <toolitem action="Find"/>
                        <separator/>
                        <toolitem action="ZoomIn"/>
                        <toolitem action="ZoomOut"/>
                        <toolitem action="ZoomFit"/>
                        <toolitem action="Zoom100"/>
                        <separator/>
                        <toolitem action="Expand"/>
                        <toolitem action="Contract"/>
                </toolbar>
        </ui>
        '''
        uimanager.add_ui_from_string(menu_ui)
        menubar = uimanager.get_widget('/MenuBar')
        main_vbox.pack_start(menubar, False, True, 0)

        # Create toolbar
        toolbar = uimanager.get_widget('/ToolBar')
        toolbar.set_style(gtk.ToolbarStyle.ICONS)
        self.toolbar = toolbar
        main_vbox.pack_start(toolbar, False, True, 0)

        # Create tab notebook
        tab_page = gtk.Notebook()
        self.tab_page = tab_page
        main_vbox.pack_start(tab_page, True, True, 0)

        # Create status bar with sunken relief
        statusbar_frame = gtk.Frame()
        statusbar_frame.set_shadow_type(gtk.ShadowType.IN)
        statusbar_frame.set_border_width(1)
        statusbar = gtk.Statusbar()
        # Reduce vertical padding to make status bar slimmer
        statusbar.set_margin_top(0)
        statusbar.set_margin_bottom(0)
        # Get the label inside the statusbar and reduce its padding
        for child in statusbar.get_children():
            if isinstance(child, gtk.Box):
                child.set_spacing(0)
                for label_child in child.get_children():
                    if isinstance(label_child, gtk.Label):
                        label_child.set_margin_top(2)
                        label_child.set_margin_bottom(2)
        statusbar_frame.add(statusbar)
        self.statusbar = statusbar
        self.statusbar_frame = statusbar_frame
        main_vbox.pack_start(statusbar_frame, False, True, 0)

        # Calculate and display boot time
        proc_tree = trace.proc_tree
        if proc_tree.idle:
            duration = proc_tree.idle
        else:
            duration = proc_tree.duration
        dur = duration / 100.0
        boot_time_str = '%02d:%05.2f' % (math.floor(dur/60), dur - 60 * math.floor(dur/60))
        statusbar.push(0, "Boot time: %s" % boot_time_str)
        GObject.timeout_add(5000, lambda: statusbar.pop(0))

        full_opts = RenderOptions(app_options)
        full_tree = PyBootchartShell(window, trace, full_opts, 3.0)
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

        # Auto-hide tab bar when there's only one tab
        show_tabs = len(self.tabs) > 1
        tab_page.set_show_tabs(show_tabs)

        # Update the toggle action to match initial state
        self.uimanager.get_action('/MenuBar/View/ShowTabs').set_active(show_tabs)

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

    def on_find(self, action):
        """Show the search bar in the current tab"""
        current_tab = self.get_current_tab()
        current_tab.show_search()

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
                # Temporarily set format to None so batch.render derives it from filename extension
                saved_format = self.app_options.format
                self.app_options.format = None
                try:
                    batch.render(writer, self.trace, self.app_options, filename)
                    self.statusbar.push(0, f"Saved to {filename}")
                    GObject.timeout_add(5000, lambda: self.statusbar.pop(0))
                finally:
                    self.app_options.format = saved_format
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

    def on_print(self, action):
        print_op = gtk.PrintOperation()
        print_op.set_n_pages(1)
        print_op.set_unit(gtk.Unit.POINTS)

        def begin_print(operation, context):
            pass

        def draw_page(operation, context, page_nr):
            cr = context.get_cairo_context()

            # Get page dimensions
            page_width = context.get_width()
            page_height = context.get_height()

            # Get chart dimensions
            current_tab = self.get_current_tab()
            options = current_tab.widget2.options
            from . import draw
            chart_width, chart_height = draw.extents(options, 1.0, self.trace)

            # Calculate scaling to fit page
            scale_x = page_width / chart_width
            scale_y = page_height / chart_height
            scale = min(scale_x, scale_y)

            # Center on page
            offset_x = (page_width - chart_width * scale) / 2
            offset_y = (page_height - chart_height * scale) / 2

            cr.translate(offset_x, offset_y)
            cr.scale(scale, scale)

            # Render the chart
            draw.render(cr, options, 1.0, self.trace)

        print_op.connect('begin-print', begin_print)
        print_op.connect('draw-page', draw_page)

        result = print_op.run(gtk.PrintOperationAction.PRINT_DIALOG, self)

        if result == gtk.PrintOperationResult.ERROR:
            error_dialog = gtk.MessageDialog(
                parent=self,
                flags=0,
                message_type=gtk.MessageType.ERROR,
                buttons=gtk.ButtonsType.OK,
                text="Print Error"
            )
            error_dialog.format_secondary_text("An error occurred while printing")
            error_dialog.run()
            error_dialog.destroy()

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

    def on_toggle_best_fit(self, action):
        # Update all tabs
        for tab in self.tabs:
            tab.on_toggle_best_fit(action)

    def on_toggle_prune_procs(self, action):
        # Update prune option
        self.app_options.prune = action.get_active()
        # Reload trace with new prune setting
        self.reload_trace()

    def on_toggle_show_kernel(self, action):
        # Update show_kernel option
        self.app_options.show_kernel = action.get_active()
        # Reload trace with new show_kernel setting
        self.reload_trace()

    def on_sort_changed(self, action, current):
        # Map radio action values to sort strategy strings
        sort_map = {0: 'pid', 1: 'start-time', 2: 'cpu-time', 3: 'end-time'}
        sort_value = current.get_current_value()
        self.app_options.proc_sort = sort_map.get(sort_value, 'pid')
        # Reload trace with new sort setting
        self.reload_trace()

    def on_toggle_tabs(self, action):
        # Toggle visibility of tab bar
        self.tab_page.set_show_tabs(action.get_active())

    def on_toggle_toolbar(self, action):
        # Toggle visibility of toolbar
        if action.get_active():
            self.toolbar.show()
        else:
            self.toolbar.hide()

    def on_toggle_statusbar(self, action):
        # Toggle visibility of status bar
        if action.get_active():
            self.statusbar_frame.show()
        else:
            self.statusbar_frame.hide()

    def update_best_fit_action(self, active):
        """Update the Best Fit menu checkbox state"""
        action = self.uimanager.get_action('/MenuBar/View/BestFit')
        if action:
            action.set_active(active)

    def reload_trace(self):
        """Reload the trace with current app_options (e.g., after changing prune setting)"""
        from . import parsing

        class Writer:
            def error(self, msg): print(msg)
            def warn(self, msg): print(msg)
            def info(self, msg): print(msg)
            def status(self, msg): print(msg)

        writer = Writer()
        # Re-parse with new options
        new_trace = parsing.Trace(writer, [self.trace.filename], self.app_options)
        self.trace = new_trace

        # Update window title
        self.set_title("Bootchart %s" % new_trace.filename)

        # Recreate all tabs with new trace
        # Remove old tabs from notebook
        while self.tab_page.get_n_pages() > 0:
            self.tab_page.remove_page(0)
        self.tabs = []

        # Recreate tabs
        full_opts = draw.RenderOptions(self.app_options)
        full_tree = PyBootchartShell(self, new_trace, full_opts, 3.0)
        self.tab_page.append_page(full_tree, gtk.Label("Full tree"))
        self.tabs = [full_tree]

        if new_trace.kernel is not None and len(new_trace.kernel) > 2:
            kernel_opts = draw.RenderOptions(self.app_options)
            kernel_opts.cumulative = False
            kernel_opts.charts = False
            kernel_opts.kernel_only = True
            kernel_tree = PyBootchartShell(self, new_trace, kernel_opts, 5.0)
            self.tab_page.append_page(kernel_tree, gtk.Label("Kernel boot"))
            self.tabs.append(kernel_tree)

        # Update tab visibility
        show_tabs = len(self.tabs) > 1
        self.tab_page.set_show_tabs(show_tabs)
        self.uimanager.get_action('/MenuBar/View/ShowTabs').set_active(show_tabs)

        # Show all new widgets
        self.tab_page.show_all()

    def on_about(self, action):
        about = gtk.AboutDialog()
        about.set_transient_for(self)
        about.set_program_name("InitViz")
        about.set_version(get_version())
        about.set_comments("Boot and init process performance visualization tool\nForked from bootchart2")
        about.set_copyright("Copyright © 2009-2010 Novell, Inc.\nCopyright © Riccardo Magliocchetti and contributors")
        about.set_license_type(gtk.License.GPL_3_0)
        about.set_website("https://github.com/finit-project/InitViz")
        about.set_website_label("InitViz on GitHub")
        about.set_authors([
            "Riccardo Magliocchetti",
            "Michael Meeks",
            "Anders Norgaard",
            "Henning Niss",
            "Scott James Remnant",
            "Ziga Mahkovec",
            "Joachim Wiberg",
            "And other contributors"
        ])
        about.set_logo_icon_name("utilities-system-monitor")

        about.run()
        about.destroy()


def show(trace, options):
    win = PyBootchartWindow(trace, options)
    win.connect('destroy', gtk.main_quit)

    def signal_handler(sig, _):
        print(f"\nReceived signal {sig}, closing...")
        win.destroy()

    signal.signal(signal.SIGINT, signal_handler)
    GObject.timeout_add(100, lambda: True)

    gtk.main()
