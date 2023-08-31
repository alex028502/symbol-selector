import subprocess
from functools import partial
import os
import gi
from collections import Counter

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, GLib, Gdk

__dir__ = os.path.dirname(__file__)

CLOCK = chr(0x1F559)


class SelectorWindow(Gtk.Window):
    def __init__(self, window_id, history_path):
        self.history_path = history_path
        orders = 5
        base = 3
        self.search_timer_id = None
        history = subprocess.run(
            ["tail", "-c", str(base**orders), self.history_path],
            stdout=subprocess.PIPE,
            text=True,
        ).stdout
        weighted_history = history
        for o in range(0, orders):
            weighted_history += weighted_history[-(base**o) :]

        self.history = dict(Counter(weighted_history))

        process = subprocess.Popen(
            ["emacs", "-Q", "--batch", "--script", "%s/symbols.el" % __dir__],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self.all_items = process.communicate()[0].strip().split("\n")

        Gtk.Window.__init__(self, title="Symbol Selector")
        self.maximize()
        self.fullscreen()
        self.window_id = window_id
        self.present()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(vbox)

        self.search_entry = Gtk.Entry()
        self.search_entry.connect("changed", self.on_search_changed)
        vbox.pack_start(self.search_entry, False, False, 0)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        vbox.pack_start(scrolled_window, True, True, 0)

        self.listbox = Gtk.ListBox()
        self.listbox.connect("row-activated", self.on_selected)
        scrolled_window.add(self.listbox)

        self.items = self.all_items
        self.search_text = ""
        self.update()

        self.search_entry.grab_focus()

    def on_selected(self, listbox, row):
        label = row.get_child()
        selected_symbol = label.get_text()[0]
        self.close()
        os.system(
            "%s/type.sh %s '%s'"
            % (
                __dir__,
                self.window_id,
                selected_symbol,
            )
        )
        with open(self.history_path, "a") as file:
            file.write(selected_symbol)

    def narrow_down(self, items, search_text):
        return list(
            filter(
                partial(check_for_terms, search_text.split()),
                items,
            )
        )

    def on_search_changed(self, entry):
        if self.search_timer_id:
            GLib.source_remove(self.search_timer_id)
        self.search_timer_id = GLib.timeout_add(
            0.2, partial(self.delayed_search, entry)
        )

    def delayed_search(self, entry):
        search_text = entry.get_text().upper()
        if search_text in self.search_text:
            self.items = self.narrow_down(self.items, search_text)
        else:
            self.items = self.narrow_down(self.all_items, search_text)

        self.search_text = search_text
        self.update()

    def update(self):
        for child in self.listbox.get_children():
            self.listbox.remove(child)

        visible_items = self.items
        visible_items = list(filter(lambda x: len(x), visible_items))
        if len(visible_items) > 2000:
            visible_items = filter(
                lambda x: x[0] in self.history,
                visible_items,
            )

        visible_items = sorted(
            visible_items,
            key=lambda x: -self.history.get(x[0], 0),
        )

        for item in visible_items:
            if item[0] in self.history:
                label = "%s (%s)" % (item, CLOCK)
            else:
                label = item

            self.listbox.add(Gtk.Label(label=label))

        self.listbox.show_all()

    def do_key_press_event(self, event):
        if event.keyval == Gdk.KEY_Escape:
            self.close()
        if event.keyval not in [Gdk.KEY_Return, Gdk.KEY_Up, Gdk.KEY_Down]:
            if not self.search_entry.is_focus():
                self.search_entry.grab_focus()
        return Gtk.Window.do_key_press_event(self, event)

    def do_focus_out_event(self, event):
        self.close()
        return Gtk.Window.do_focus_out_event(self, event)


def check_for_terms(terms, text):
    for term in terms:
        if term not in text:
            return False
    return True


def main():
    history_path = os.path.expanduser("~/.symbols/history.txt")
    os.system("mkdir -p %s && touch %s" % (os.path.dirname(history_path), history_path))

    window_id = subprocess.getoutput("xdotool getwindowfocus")
    selector_window = SelectorWindow(window_id, history_path)
    selector_window.show_all()
    selector_window.connect("destroy", lambda _: Gtk.main_quit())


main()
Gtk.main()
