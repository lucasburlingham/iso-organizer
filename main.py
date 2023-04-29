import os
import datetime
import time
import sys
import sqlite3
import configparser
import gi
gi.require_version("Gtk", "4.0")

from gi.repository import GLib, Gtk



# import helper files
import modules.checkSettings as checkSettings
import modules.getfiles as getfiles


class MyApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.jovarkos.imagesorter")
        GLib.set_application_name("Image Sorter")
        checkSettings()

    def do_activate(self):
        window = Gtk.ApplicationWindow(
            application=self, title="Image Sorter", default_width=700, default_height=500)
        window.present()


app = MyApplication()
exit_status = app.run(sys.argv)
sys.exit(exit_status)
