#!/usr/bin/python3

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GLib", "2.0")
gi.require_version("Flatpak", "1.0")
from gi.repository import Gtk, Gio, Gdk
import sqlite3
import requests
from urllib.parse import quote_plus
import libflatpak_query
from libflatpak_query import AppstreamSearcher, Flatpak
import json

class MainWindow(Gtk.Window):
    def __init__(self):
        super().__init__()

        # Store search results as an instance variable
        self.search_results = []  # Initialize empty list

        # Set window size
        self.set_default_size(1280, 720)

        # Define category groups and their titles
        self.category_groups = {
            'collections': {
                'trending': 'Trending',
                'popular': 'Popular',
                'recently-added': 'New',
                'recently-updated': 'Updated'
            },
            'categories': {
                'office': 'Productivity',
                'graphics': 'Graphics & Photography',
                'audiovideo': 'Audio & Video',
                'education': 'Education',
                'network': 'Networking',
                'game': 'Games',
                'development': 'Developer Tools',
                'science': 'Science',
                'system': 'System',
                'utility': 'Utilities'
            }
        }

        # Define subcategories for Games
        self.subcategories = {
            'Emulator': 'Emulators',
            'Launcher': 'Game Launchers',
            'Tool': 'Game Tools'
        }

        # Add CSS provider for custom styling
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data("""
            .dark-header {
                background-color: #333333;
                padding: 6px;
                margin: 0;
            }

            .dark-category-button {
                border: 0px;
                padding: 6px;
                margin: 0;
                background: none;
            }

            .dark-category-button-active {
                background-color: #18A3FF;
                color: white;
            }
        """)

        # Add CSS provider to the default screen
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            600
        )

        # Create main layout
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(self.main_box)

        # Create panels
        self.create_panels()

        # Select Trending by default
        self.select_default_category()

        self.refresh_data()

    def refresh_data(self):

        total_categories = sum(len(categories) for categories in self.category_groups.values())
        current_category = 0
        msg = "Fetching metadata, please wait..."
        dialog = Gtk.Dialog(
            title=msg,
            parent=self,
            modal=True,
            destroy_with_parent=True
        )

        # Set dialog size
        dialog.set_size_request(400, 100)

        # Create progress bar
        progress_bar = Gtk.ProgressBar()
        progress_bar.set_text(msg)

        # Add progress bar to dialog
        dialog.vbox.pack_start(progress_bar, True, True, 0)
        dialog.vbox.set_spacing(12)

        # Show the dialog and all its children
        dialog.show_all()

        # Search for each app in local repositories
        searcher = AppstreamSearcher()
        searcher.add_installation(Flatpak.Installation.new_user())

        for group_name, categories in self.category_groups.items():
            # Process categories one at a time to keep GUI responsive
            for category, title in categories.items():

                # Current offline-only mode. Later we will check metadata date and refresh if need
                apps = searcher.get_all_apps('flathub')
                for app in apps:
                    details = app.get_details()
                    if category in details['categories']:
                        search_result = searcher.search_flatpak(details['name'], 'flathub')
                        self.search_results.extend(search_result)

                # Planned code for metadata refresh, not ready yet
                # Try to get apps from Flathub API if internet is available
                #if self.check_internet():
                #    api_data = self.fetch_flathub_category_apps(category)
                #    if api_data:
                #        apps = api_data['hits']
                #
                #        for app in apps:
                #            app_id = app['app_id']
                #            # Search for the app in local repositories
                #            search_result = searcher.search_flatpak(app_id, 'flathub')
                #            self.search_results.extend(search_result)
                #else:
                #    apps = searcher.get_all_apps('flathub')
                #    for app in apps:
                #        details = app.get_details()
                #        if category in details['categories']:
                #            search_result = searcher.search_flatpak(details['name'], 'flathub')
                #            self.search_results.extend(search_result)

                current_category += 1

                # Update progress bar
                progress = (current_category / total_categories) * 100
                progress_bar.set_fraction(progress / 100)

                # Force GTK to process events
                while Gtk.events_pending():
                    Gtk.main_iteration_do(False)

        dialog.destroy()

    def create_panels(self):
        # Create left panel with grouped categories
        self.create_grouped_category_panel("Categories", self.category_groups)

        # Create right panel
        self.right_panel = self.create_applications_panel("Applications")

    def create_grouped_category_panel(self, title, groups):
        # Create scrollable area
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_size_request(300, -1)  # Set fixed width
        scrolled_window.set_hexpand(False)  # Don't expand horizontally
        scrolled_window.set_vexpand(True)   # Expand vertically

        # Create container for categories
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        container.set_spacing(6)
        container.set_border_width(6)
        container.set_halign(Gtk.Align.FILL)  # Fill horizontally
        container.set_valign(Gtk.Align.START)  # Align to top

        # Dictionary to store category widgets
        self.category_widgets = {}

        # Add group headers and categories
        for group_name, categories in groups.items():
            # Create a box for the header
            header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            header_box.get_style_context().add_class("dark-header")
            header_box.set_hexpand(True)  # Make the box expand horizontally

            # Create the label
            group_header = Gtk.Label(label=group_name.upper())
            group_header.get_style_context().add_class("title-2")
            group_header.set_halign(Gtk.Align.START)

            # Add the label to the box
            header_box.pack_start(group_header, False, False, 0)

            # Add the box to the container
            container.pack_start(header_box, False, False, 0)

            # Store widgets for this group
            self.category_widgets[group_name] = []

            # Add categories in the group
            for category, display_title in categories.items():
                # Create a clickable box for each category
                category_box = Gtk.EventBox()
                category_box.set_hexpand(True)
                category_box.set_halign(Gtk.Align.FILL)
                category_box.set_margin_top(2)
                category_box.set_margin_bottom(2)

                # Create label for the category
                category_label = Gtk.Label(label=display_title)
                category_label.set_halign(Gtk.Align.START)
                category_label.set_hexpand(True)
                category_label.get_style_context().add_class("dark-category-button")

                # Add label to the box
                category_box.add(category_label)

                # Connect click event
                category_box.connect("button-release-event",
                                lambda widget, event, cat=category, grp=group_name:
                                self.on_category_clicked(cat, grp))

                # Store widget in group
                self.category_widgets[group_name].append(category_box)
                container.pack_start(category_box, False, False, 0)

        # Add container to scrolled window
        scrolled_window.add(container)

        # Pack the scrolled window directly into main box
        self.main_box.pack_start(scrolled_window, False, False, 0)

    def on_category_clicked(self, category, group):
        # Remove active state from all categories in the same group
        for widget in self.category_widgets[group]:
            widget.get_style_context().remove_class("dark-category-button-active")

        # Add active state to the clicked category
        display_title = self.category_groups[group][category]
        for widget in self.category_widgets[group]:
            if widget.get_children()[0].get_label() == display_title:
                widget.get_style_context().add_class("dark-category-button-active")
                break

        self.show_category_apps(category)

    def create_applications_panel(self, title):
        # Create right panel
        self.right_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.right_panel.set_size_request(-1, -1)

        # Create scrollable area
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_hexpand(True)
        scrolled_window.set_vexpand(True)

        # Create container for applications
        self.right_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.right_container.set_spacing(6)
        self.right_container.set_border_width(6)

        scrolled_window.add(self.right_container)
        self.main_box.pack_end(scrolled_window, True, True, 0)
        return self.right_container

    def check_internet(self):
        """Check if internet connection is available."""
        try:
            requests.head('https://flathub.org', timeout=3)
            return True
        except requests.ConnectionError:
            return False

    def fetch_flathub_category_apps(self, category):
        """Fetch applications from Flathub API for the specified category."""
        try:
            # URL encode the category to handle special characters
            encoded_category = quote_plus(category)

            # Determine the base URL based on category type
            if category in self.category_groups['collections']:
                url = f"https://flathub.org/api/v2/collection/{encoded_category}"
            else:
                url = f"https://flathub.org/api/v2/collection/category/{encoded_category}"

            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to fetch apps: Status code {response.status_code}")
                return None

        except requests.RequestException as e:
            print(f"Error fetching apps: {str(e)}")
            return None


    def show_category_apps(self, category):
        # Clear existing content
        for child in self.right_container.get_children():
            child.destroy()

        # Filter apps based on category
        apps = [app for app in self.search_results if category in app.get_details()['categories']]

        # Display each application
        for app in apps:
            details = app.get_details()

            # Create application container
            app_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            app_container.set_spacing(12)
            app_container.set_margin_top(6)
            app_container.set_margin_bottom(6)

            # Add icon placeholder
            icon_box = Gtk.Box()
            icon_box.set_size_request(148, -1)

            # Create and add the icon
            icon = Gtk.Image.new_from_file(f"{details['icon_path_64']}/{details['icon_filename']}")
            icon.set_size_request(48, 48)  # Set a reasonable size for the icon
            icon_box.pack_start(icon, True, True, 0)  # Add icon to the box

            # Create right side layout for text
            right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            right_box.set_spacing(4)
            right_box.set_hexpand(True)

            # Add title
            title_label = Gtk.Label(label=details['name'])
            title_label.get_style_context().add_class("title-1")
            title_label.set_halign(Gtk.Align.START)
            title_label.set_hexpand(True)

            # Add summary
            desc_label = Gtk.Label(label=details['summary'])
            desc_label.set_halign(Gtk.Align.START)
            desc_label.set_hexpand(True)
            desc_label.set_line_wrap(True)
            desc_label.set_line_wrap_mode(Gtk.WrapMode.WORD)
            desc_label.get_style_context().add_class("dim-label")

            # Add separator
            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)

            # Add to container
            right_box.pack_start(title_label, False, False, 0)
            right_box.pack_start(desc_label, False, False, 0)
            app_container.pack_start(icon_box, False, False, 0)
            app_container.pack_start(right_box, True, True, 0)
            self.right_container.pack_start(app_container, False, False, 0)
            self.right_container.pack_start(separator, False, False, 0)

        self.right_container.show_all()  # Show all widgets after adding them

    def select_default_category(self):
        # Select Trending by default
        if 'collections' in self.category_widgets and self.category_widgets['collections']:
            self.on_category_clicked('trending', 'collections')

def main():
    app = MainWindow()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
