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
            }
            .dark-category-button,
            .dark-category-button:hover,
            .dark-category-button:focus,
            .dark-category-button:active {
                background: none;
                border: none;
                padding: 0;
                outline: none;
                box-shadow: none;
                transition: none;
                -webkit-appearance: none;
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

        self.refresh_database()

        # Select Trending by default
        self.select_default_category()

    def refresh_database(self):
        # Try to get apps from Flathub API if internet is available
        if self.check_internet():

            total_categories = sum(len(categories) for categories in self.category_groups.values())
            current_category = 0
            msg = "Updating metadata, please wait..."
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

            for group_name, categories in self.category_groups.items():
                # Process categories one at a time to keep GUI responsive
                for category, title in categories.items():
                    api_data = self.fetch_flathub_category_apps(category)
                    if api_data:
                        apps = api_data['hits']

                        # Create database if it doesn't exist
                        db_path = 'flatshop_db'
                        create_repo_table(db_path, 'flathub')

                        # Search for each app in local repositories
                        searcher = AppstreamSearcher()
                        searcher.add_installation(Flatpak.Installation.new_user())

                        for app in apps:
                            app_id = app['app_id']
                            # Search for the app in local repositories
                            search_results = searcher.search_flatpak(app_id, 'flathub')

                            # Store category results in database
                            self.update_database(category, db_path, app_id, search_results)

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

        # Dictionary to store buttons grouped by category
        self.category_buttons = {}

        # Add group headers and buttons
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

            # Store buttons for this group
            self.category_buttons[group_name] = []

            # Add categories in the group
            for category, display_title in categories.items():
                # Create clickable button for each category
                button = Gtk.ToggleButton(label=display_title)
                button.get_style_context().remove_class("dark-header")
                button.get_style_context().add_class("dark-category-button")
                button.set_halign(Gtk.Align.START)  # Left align button
                button.set_hexpand(True)  # Expand horizontally
                button.connect("clicked", self.on_category_button_clicked, category, group_name)

                # Store button in group
                self.category_buttons[group_name].append(button)
                container.pack_start(button, False, False, 2)

        # Add container to scrolled window
        scrolled_window.add(container)

        # Pack the scrolled window directly into main box
        self.main_box.pack_start(scrolled_window, False, False, 0)

    def on_category_button_clicked(self, button, category, group):
        # Uncheck all other buttons in the same group
        for btn in self.category_buttons[group]:
            if btn != button:
                btn.set_active(False)
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

    def update_collection_status(self, category, db_path, app_id):
        """Updates the trending status for a specific application."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        category = category.replace('-', '_').lower()

        # Use string formatting to properly identify the column name
        query = f"""
            UPDATE flathub
            SET {category} = 1
            WHERE id = '{app_id}'
        """

        try:
            cursor.execute(query)
            conn.commit()
            print(f"Collection {category} updated for app_id: {app_id}")
        except sqlite3.Error as e:
            print(f"Error updating database: {str(e)}")
        finally:
            conn.close()

    def update_database(self, category, db_path, app_id, search_results):
        """Update database."""

        # Process each app
        for result in search_results:
            app_data = result.get_details()

            # Store app data
            if category in self.category_groups['categories']:
                store_app_data(db_path, 'flathub', app_data)

            if category in self.category_groups['collections']:
                self.update_collection_status(category, db_path, app_id)

    def show_category_apps(self, category):
        # Clear existing content
        for child in self.right_container.get_children():
            child.destroy()

        # Now pull the new info from our local database
        try:
            conn = sqlite3.connect('flatshop_db')
            cursor = conn.cursor()
            if category in self.category_groups['categories']:
                cursor.execute("""
                    SELECT id, name, summary, description, icon_path_64
                    FROM flathub
                    WHERE ? IN (SELECT value FROM json_each(categories))
                    ORDER BY name ASC
                """, (category,))
            elif category in self.category_groups['collections']:
                category = category.replace('-', '_').lower()
                # Use string formatting to properly identify the column name
                query = f"""
                    SELECT id, name, summary, description, icon_path_64
                    FROM flathub
                    WHERE {category} = 1
                    ORDER BY name ASC
                """
                print(query)
                cursor.execute(query)


            # Display each application
            for id, name, summary, description, icon_path_64 in cursor.fetchall():
                # Create application container
                app_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                app_container.set_spacing(12)
                app_container.set_margin_top(6)
                app_container.set_margin_bottom(6)

                # Add icon placeholder
                icon_box = Gtk.Box()
                icon_box.set_size_request(148, -1)

                # Create and add the icon
                icon = Gtk.Image.new_from_file(f"{icon_path_64}")
                icon.set_size_request(48, 48)  # Set a reasonable size for the icon
                icon_box.pack_start(icon, True, True, 0)  # Add icon to the box

                # Create right side layout for text
                right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                right_box.set_spacing(4)
                right_box.set_hexpand(True)

                # Add title
                title_label = Gtk.Label(label=name)
                title_label.get_style_context().add_class("title-1")
                title_label.set_halign(Gtk.Align.START)
                title_label.set_hexpand(True)

                # Add summary
                desc_label = Gtk.Label(label=summary)
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

        except sqlite3.Error as e:
            error_label = Gtk.Label(label=f"Error loading applications: {str(e)}")
            error_label.get_style_context().add_class("error-label")
            error_label.set_halign(Gtk.Align.CENTER)
            self.right_container.pack_start(error_label, False, False, 0)

        finally:
            conn.close()
            self.right_container.show_all()  # Show all widgets after adding them

    def select_default_category(self):
        # Select Trending by default
        if 'collections' in self.category_buttons and self.category_buttons['collections']:
            trending_button = self.category_buttons['collections'][0]
            trending_button.set_active(True)
            self.on_category_button_clicked(trending_button, 'trending', 'collections')

def create_repo_table(db_path, repo_name):
    """Create a table for storing app data from a specific repository."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create table with all fields from AppStreamPackage
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {repo_name} (
                id TEXT PRIMARY KEY,
                name TEXT,
                summary TEXT,
                description TEXT,
                version TEXT,
                icon_url TEXT,
                icon_path_128 TEXT,
                icon_path_64 TEXT,
                icon_filename TEXT,
                developer TEXT,
                categories TEXT,
                bundle_id TEXT,
                repo_name TEXT,
                match_type TEXT,
                urls TEXT,
                trending INTEGER DEFAULT 0,
                popular INTEGER DEFAULT 0,
                recently_added INTEGER DEFAULT 0,
                recently_updated INTEGER DEFAULT 0,
                FOREIGN KEY (id) REFERENCES applications (app_id)
            )
        """)

        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error creating table: {str(e)}")
        return False
    finally:
        conn.close()

def store_app_data(db_path, repo_name, app_data):
    """Store app data in the SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Convert URLs dictionary to JSON string for storage
        urls_json = json.dumps(app_data['urls'])
        categories_json = json.dumps(app_data['categories'])

        # Insert data into the repository table
        cursor.execute(f"""
            INSERT OR REPLACE INTO {repo_name} (
                id, name, summary, description, version,
                icon_url, icon_path_128, icon_path_64,
                icon_filename, developer, categories,
                bundle_id, repo_name, match_type, urls,
                trending, popular, recently_added, recently_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            app_data['id'],
            app_data['name'],
            app_data['summary'],
            app_data['description'],
            app_data['version'],
            app_data['icon_url'],
            app_data['icon_path_128'],
            app_data['icon_path_64'],
            app_data['icon_filename'],
            app_data['developer'],
            categories_json,
            app_data['bundle_id'],
            repo_name,
            app_data['match_type'],
            urls_json,
            0,
            0,
            0,
            0
        ))

        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error storing app data: {str(e)}")
        return False
    finally:
        conn.close()

def main():
    app = MainWindow()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
