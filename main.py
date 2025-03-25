#!/usr/bin/python3

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GLib", "2.0")
gi.require_version("Flatpak", "1.0")
from gi.repository import Gtk, Gio, Gdk, GLib
import libflatpak_query
import json
import threading

class MainWindow(Gtk.Window):
    def __init__(self):
        super().__init__()

        # Store search results as an instance variable
        self.category_results = []  # Initialize empty list
        self.collection_results = []  # Initialize empty list
        self.installed_results = []  # Initialize empty list
        self.updates_results = []  # Initialize empty list
        self.system_mode = False
        self.current_page = None  # Track current page
        self.current_group = None  # Track current group (system/collections/categories)

        # Set window size
        self.set_default_size(1280, 720)

        # Define category groups and their titles
        self.category_groups = {
            'system': {
                'installed': 'Installed',
                'updates': 'Updates',
                'repositories': 'Repositories'
            },
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
            .panel-header {
                font-size: 24px;
                font-weight: bold;
                padding: 12px;
                color: white;
            }
            .repo-list-header {
                font-size: 18px;
                padding: 5px;
                color: white;
            }
            .app-list-header {
                font-size: 18px;
                color: white;
                padding-top: 4px;
                padding-bottom: 4px;
            }
            .app-list-summary {
                padding-top: 2px;
                padding-bottom: 2px;
            }
            .app-page-header {
                font-size: 24px;
                font-weight: bold;
                padding: 12px;
                color: white;
            }
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
            .dark-remove-button {
                background-color: #ff4444;
                color: white;
                border: none;
                padding: 6px;
                margin: 0;
            }
            .dark-install-button {
                background-color: #18A3FF;
                color: white;
                border: none;
                padding: 6px;
                margin: 0;
            }
            .repo-item {
                padding: 6px;
                margin: 2px;
                border-bottom: 1px solid #eee;
            }
            .repo-delete-button {
                background-color: #ff4444;
                color: white;
                border: none;
                padding: 6px;
                margin-left: 6px;
            }
            .search-entry {
                padding: 5px;
                border-radius: 4px;
                border: 1px solid #ccc;
            }

            .search-entry:focus {
                border-color: #18A3FF;
                box-shadow: 0 0 0 2px rgba(24, 163, 255, 0.2);
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

        self.refresh_data()

        # Select Trending by default
        self.select_default_category()

    def populate_repo_dropdown(self):
        # Get list of repositories
        libflatpak_query.repolist(self.system_mode)
        repos = libflatpak_query.repolist()

        # Clear existing items
        self.repo_dropdown.remove_all()

        # Add repository names
        for repo in repos:
            self.repo_dropdown.append_text(repo.get_name())

        # Connect selection changed signal
        self.repo_dropdown.connect("changed", self.on_repo_selected)

    def on_repo_selected(self, dropdown):
        active_index = dropdown.get_active()
        if active_index != -1:
            self.selected_repo = dropdown.get_model()[active_index][0]
            print(f"Selected repository: {self.selected_repo}")

    def refresh_data(self):
        # Create dialog and progress bar
        dialog = Gtk.Dialog(
            title="Fetching metadata, please wait...",
            parent=self,
            modal=True,
            destroy_with_parent=True
        )
        dialog.set_size_request(400, 100)

        progress_bar = Gtk.ProgressBar()
        progress_bar.set_text("Initializing...")
        progress_bar.set_show_text(True)
        dialog.vbox.pack_start(progress_bar, True, True, 0)
        dialog.vbox.set_spacing(12)

        # Show the dialog
        dialog.show_all()

        searcher = libflatpak_query.get_reposearcher(self.system_mode)

        # Define thread target function
        def refresh_target():
            try:
                category_results, collection_results, installed_results, updates_results = searcher.retrieve_metadata(self.system_mode)
                self.category_results = category_results
                self.collection_results = collection_results
                self.installed_results = installed_results
                self.updates_results = updates_results
            except Exception as e:
                message_type = Gtk.MessageType.ERROR
                dialog = Gtk.MessageDialog(
                    transient_for=None,  # Changed from self
                    modal=True,
                    destroy_with_parent=True,
                    message_type=message_type,
                    buttons=Gtk.ButtonsType.OK,
                    text=f"Error updating progress: {str(e)}"
                )
                dialog.run()
                dialog.destroy()

        # Start the refresh thread
        refresh_thread = threading.Thread(target=refresh_target)
        refresh_thread.start()
        def update_progress():
            while refresh_thread.is_alive():
                progress_bar.set_text("Fetching...")
                progress = searcher.refresh_progress
                progress_bar.set_fraction(progress / 100)
                return True
            else:
                progress_bar.set_fraction(100 / 100)
                dialog.destroy()

        # Start the progress update timer
        GLib.timeout_add_seconds(0.5, update_progress)
        dialog.run()
        if not refresh_thread.is_alive() and dialog.is_active():
            dialog.destroy()

    def refresh_local(self):
        # Create dialog and progress bar
        dialog = Gtk.Dialog(
            title="Refreshing local data, please wait...",
            parent=self,
            modal=True,
            destroy_with_parent=True
        )
        dialog.set_size_request(400, 100)

        progress_bar = Gtk.ProgressBar()
        progress_bar.set_text("Initializing...")
        progress_bar.set_show_text(True)
        dialog.vbox.pack_start(progress_bar, True, True, 0)
        dialog.vbox.set_spacing(12)

        # Show the dialog
        dialog.show_all()

        searcher = libflatpak_query.get_reposearcher(self.system_mode)

        # Define thread target function
        def refresh_target():
            try:
                installed_results, updates_results = searcher.refresh_local(self.system_mode)
                self.installed_results = installed_results
                self.updates_results = updates_results
            except Exception as e:
                message_type = Gtk.MessageType.ERROR
                dialog = Gtk.MessageDialog(
                    transient_for=None,  # Changed from self
                    modal=True,
                    destroy_with_parent=True,
                    message_type=message_type,
                    buttons=Gtk.ButtonsType.OK,
                    text=f"Error updating progress: {str(e)}"
                )
                dialog.run()
                dialog.destroy()

        # Start the refresh thread
        refresh_thread = threading.Thread(target=refresh_target)
        refresh_thread.start()
        def update_progress():
            while refresh_thread.is_alive():
                progress_bar.set_text("Refreshing...")
                progress = searcher.refresh_progress
                progress_bar.set_fraction(progress / 100)
                return True
            else:
                progress_bar.set_fraction(100 / 100)
                dialog.destroy()

        # Start the progress update timer
        GLib.timeout_add_seconds(0.5, update_progress)
        dialog.run()
        if not refresh_thread.is_alive() and dialog.is_active():
            dialog.destroy()

    def create_panels(self):
        # Check if panels already exist
        if hasattr(self, 'left_panel') and self.left_panel.get_parent():
            self.main_box.remove(self.left_panel)

        if hasattr(self, 'right_panel') and self.right_panel.get_parent():
            self.main_box.remove(self.right_panel)

        # Create right panel
        self.right_panel = self.create_applications_panel("Applications")

        # Create left panel with grouped categories
        self.left_panel = self.create_grouped_category_panel("Categories", self.category_groups)

        # Pack the panels with proper expansion
        self.main_box.pack_end(self.right_panel, True, True, 0)    # Right panel expands both ways
        self.main_box.pack_start(self.left_panel, False, False, 0)  # Left panel doesn't expand

    def create_grouped_category_panel(self, title, groups):

        # Create container for categories
        panel_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        panel_container.set_spacing(6)
        panel_container.set_border_width(6)
        panel_container.set_size_request(300, -1)  # Set fixed width
        panel_container.set_hexpand(False)
        panel_container.set_vexpand(True)
        panel_container.set_halign(Gtk.Align.FILL)  # Fill horizontally
        panel_container.set_valign(Gtk.Align.FILL)  # Align to top

        # Add search bar
        self.searchbar = Gtk.SearchBar()  # Use self.searchbar instead of searchbar
        self.searchbar.set_hexpand(True)
        self.searchbar.set_margin_bottom(6)

        # Create search entry with icon
        searchentry = Gtk.SearchEntry()
        searchentry.set_placeholder_text("Search applications...")
        searchentry.set_icon_from_gicon(Gtk.EntryIconPosition.PRIMARY,
                                    Gio.Icon.new_for_string('search'))

        # Connect search entry signals
        searchentry.connect("search-changed", self.on_search_changed)
        searchentry.connect("activate", self.on_search_activate)

        # Connect search entry to search bar
        self.searchbar.connect_entry(searchentry)
        self.searchbar.add(searchentry)

        # Create scrollable area
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_hexpand(True)
        scrolled_window.set_vexpand(True)   # Expand vertically
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        # Create container for categories
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        container.set_spacing(6)
        container.set_border_width(6)
        container.set_halign(Gtk.Align.FILL)  # Fill horizontally
        container.set_valign(Gtk.Align.START)  # Align to top
        container.set_hexpand(True)
        container.set_vexpand(False)   # Expand vertically

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
        panel_container.pack_start(self.searchbar, False, False, 0)
        panel_container.pack_start(scrolled_window, True, True, 0)


        self.searchbar.set_search_mode(True)
        return panel_container
        #self.searchbar.show_all()

    def on_search_changed(self, searchentry):
        """Handle search text changes"""
        search_term = searchentry.get_text().lower()
        if not search_term:
            # Reset to showing all categories when search is empty
            self.show_category_apps(self.current_category)
            return

        # Combine all searchable fields
        searchable_items = []
        for app in self.all_apps:
            details = app.get_details()
            searchable_items.append({
                'text': f"{details['name']} {details['description']} {details['categories']}".lower(),
                'app': app
            })

        # Filter results
        filtered_apps = [item['app'] for item in searchable_items
                        if search_term in item['text']]

        # Show search results
        self.show_search_results(filtered_apps)

    def on_search_activate(self, searchentry):
        """Handle Enter key press in search"""
        self.on_search_changed(searchentry)

    def show_search_results(self, apps):
        """Display search results in the right panel"""
        # Clear existing content
        for child in self.right_container.get_children():
            child.destroy()

        # Display each application
        for app in apps:
            details = app.get_details()
            is_installed = details['id'] in installed_package_ids
            is_updatable = details['id'] in updatable_package_ids

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
            icon.set_size_request(48, 48)
            icon_box.pack_start(icon, True, True, 0)

            # Create right side layout for text
            right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            right_box.set_spacing(4)
            right_box.set_hexpand(True)

            # Add title
            title_label = Gtk.Label(label=details['name'])
            title_label.get_style_context().add_class("app-list-header")
            title_label.set_halign(Gtk.Align.START)
            title_label.set_yalign(0.5)  # Use yalign instead of valign
            title_label.set_hexpand(True)

            # Add summary
            desc_label = Gtk.Label(label=details['summary'])
            desc_label.set_halign(Gtk.Align.START)
            desc_label.set_yalign(0.5)  # Use yalign instead of valign
            desc_label.set_hexpand(True)
            desc_label.set_line_wrap(True)
            desc_label.set_line_wrap_mode(Gtk.WrapMode.WORD)
            desc_label.get_style_context().add_class("dim-label")
            desc_label.get_style_context().add_class("app-list-summary")

            # Create buttons box
            buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            buttons_box.set_spacing(6)
            buttons_box.set_margin_top(4)
            buttons_box.set_halign(Gtk.Align.END)

            # Install/Remove button
            if is_installed:
                button = self.create_button(
                    self.on_remove_clicked,
                    app,
                    None,
                    condition=lambda x: True
                )
                remove_icon = Gio.Icon.new_for_string('list-remove')
                button.set_image(Gtk.Image.new_from_gicon(remove_icon, Gtk.IconSize.BUTTON))
                button.get_style_context().add_class("dark-remove-button")
            else:
                button = self.create_button(
                    self.on_install_clicked,
                    app,
                    None,
                    condition=lambda x: True
                )
                install_icon = Gio.Icon.new_for_string('list-add')
                button.set_image(Gtk.Image.new_from_gicon(install_icon, Gtk.IconSize.BUTTON))
                button.get_style_context().add_class("dark-install-button")
            buttons_box.pack_end(button, False, False, 0)

            # Add Update button if available
            if is_updatable:
                update_button = self.create_button(
                    self.on_update_clicked,
                    app,
                    None,
                    condition=lambda x: True
                )
                update_icon = Gio.Icon.new_for_string('synchronize')
                update_button.set_image(Gtk.Image.new_from_gicon(update_icon, Gtk.IconSize.BUTTON))
                update_button.get_style_context().add_class("dark-install-button")
                buttons_box.pack_end(update_button, False, False, 0)

            # Details button
            details_btn = self.create_button(
                self.on_details_clicked,
                app,
                None
            )
            details_icon = Gio.Icon.new_for_string('question')
            details_btn.set_image(Gtk.Image.new_from_gicon(details_icon, Gtk.IconSize.BUTTON))
            details_btn.get_style_context().add_class("dark-install-button")
            buttons_box.pack_end(details_btn, False, False, 0)

            # Add widgets to right box
            right_box.pack_start(title_label, False, False, 0)
            right_box.pack_start(desc_label, False, False, 0)
            right_box.pack_start(buttons_box, False, True, 0)

            # Add separator
            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)

            # Add to container
            app_container.pack_start(icon_box, False, False, 0)
            app_container.pack_start(right_box, True, True, 0)
            self.right_container.pack_start(app_container, False, False, 0)
            self.right_container.pack_start(separator, False, False, 0)

        self.right_container.show_all()

    def on_category_clicked(self, category, group):
        # Remove active state from all widgets in all groups
        for group_name in self.category_widgets:
            for widget in self.category_widgets[group_name]:
                widget.get_style_context().remove_class("dark-category-button-active")

        # Add active state to the clicked category
        display_title = self.category_groups[group][category]
        for widget in self.category_widgets[group]:
            if widget.get_children()[0].get_label() == display_title:
                widget.get_style_context().add_class("dark-category-button-active")
                break
        self.current_page = category
        self.current_group = group
        self.update_category_header(category)
        self.show_category_apps(category)

    def refresh_current_page(self):
        """Refresh the currently displayed page"""
        if self.current_page and self.current_group:
            self.on_category_clicked(self.current_page, self.current_group)

    def update_category_header(self, category):
        """Update the category header text based on the selected category."""
        if category in self.category_groups['collections']:
            display_title = self.category_groups['collections'][category]
        elif category in self.category_groups['categories']:
            display_title = self.category_groups['categories'][category]
        elif category in self.subcategories:
            display_title = self.subcategories[category]
        else:
            display_title = category.capitalize()

        self.category_header.set_label(display_title)

    def create_applications_panel(self, title):
        # Create right panel
        self.right_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Add category header
        self.category_header = Gtk.Label(label="")
        self.category_header.get_style_context().add_class("panel-header")
        self.category_header.set_hexpand(True)
        self.category_header.set_halign(Gtk.Align.START)
        self.right_panel.pack_start(self.category_header, False, False, 0)

        # Create scrollable area
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_hexpand(True)
        scrolled_window.set_vexpand(True)

        # Create container for applications
        self.right_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.right_container.set_spacing(6)
        self.right_container.set_border_width(6)
        scrolled_window.add(self.right_container)

        self.right_panel.pack_start(scrolled_window, True, True, 0)

        return self.right_panel

    # Create and connect buttons
    def create_button(self, callback, app, label=None, condition=None):
        """Create a button with optional visibility condition"""
        button = Gtk.Button()
        if label:
            button = Gtk.Button(label=label)
        button.get_style_context().add_class("app-button")
        if condition is not None:
            if not condition(app):
                return None
        button.connect("clicked", callback, app)
        return button

    def clear_container(self, container):
        """Clear all widgets from a container"""
        for child in container.get_children():
            child.destroy()

    def show_category_apps(self, category):
        # Clear existing content properly
        for child in self.right_container.get_children():
            child.destroy()

        # Initialize apps list
        apps = []

        # Load system data
        if 'installed' in category:
            apps.extend([app for app in self.installed_results])
        if 'updates' in category:
            apps.extend([app for app in self.updates_results])

        # Track installed package IDs for quick lookup
        installed_package_ids = {app.get_details()['id'] for app in self.installed_results}
        updatable_package_ids = {app.get_details()['id'] for app in self.updates_results}

        # Load collections data
        try:
            with open("collections_data.json", 'r', encoding='utf-8') as f:
                collections_data = json.load(f)

                # Find the specific category in collections data
                category_entry = next((
                    entry for entry in collections_data
                    if entry['category'] == category
                ), None)

                if category_entry:
                    # Get all app IDs in this category
                    app_ids_in_category = [
                        hit['app_id'] for hit in category_entry['data']['hits']
                    ]

                    # Filter apps based on presence in category
                    apps.extend([
                        app for app in self.collection_results
                        if app.get_details()['id'] in app_ids_in_category
                    ])
                else:
                    # Fallback to previous behavior if category isn't in collections
                    apps.extend([
                        app for app in self.collection_results
                        if category in app.get_details()['categories']
                    ])

        except (IOError, json.JSONDecodeError) as e:
            print(f"Error reading collections data: {str(e)}")
            apps.extend([
                app for app in self.collection_results
                if category in app.get_details()['categories']
            ])

        if 'repositories' in category:
            # Clear existing content
            for child in self.right_container.get_children():
                child.destroy()

            # Create header bar
            header_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            header_bar.set_hexpand(True)
            header_bar.set_spacing(6)
            header_bar.set_border_width(6)

            # Create left label
            left_label = Gtk.Label(label="On/Off")
            left_label.get_style_context().add_class("repo-list-header")
            left_label.set_halign(Gtk.Align.START)  # Align left
            header_bar.pack_start(left_label, True, True, 0)

            # Center container to fix "URL" label alignment
            center_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            center_container.set_halign(Gtk.Align.START)  # Align left

            # Create center label
            center_label = Gtk.Label(label="URL")
            center_label.get_style_context().add_class("repo-list-header")
            center_label.set_halign(Gtk.Align.START)  # Align center

            center_container.pack_start(center_label, True, True, 0)
            header_bar.pack_start(center_container, True, True, 0)

            # Create right label
            right_label = Gtk.Label(label="+/-")
            right_label.get_style_context().add_class("repo-list-header")
            right_label.set_halign(Gtk.Align.END)   # Align right
            header_bar.pack_end(right_label, False, False, 0)

            # Add header bar to container
            self.right_container.pack_start(header_bar, False, False, 0)

            # Get list of repositories
            repos = libflatpak_query.repolist(self.system_mode)

            # Create a scrolled window for repositories
            scrolled_window = Gtk.ScrolledWindow()
            scrolled_window.set_hexpand(True)
            scrolled_window.set_vexpand(True)

            # Create container for repositories
            repo_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            repo_container.set_spacing(6)
            repo_container.set_border_width(6)

            # Add repository button
            add_repo_button = Gtk.Button()
            add_icon = Gio.Icon.new_for_string('list-add')
            add_repo_button.set_image(Gtk.Image.new_from_gicon(add_icon, Gtk.IconSize.BUTTON))
            add_repo_button.get_style_context().add_class("dark-install-button")
            add_repo_button.connect("clicked", self.on_add_repo_button_clicked)

            add_flathub_repo_button = Gtk.Button(label="Add Flathub Repo")
            add_flathub_repo_button.get_style_context().add_class("dark-install-button")
            add_flathub_repo_button.connect("clicked", self.on_add_flathub_repo_button_clicked)

            add_flathub_beta_repo_button = Gtk.Button(label="Add Flathub Beta Repo")
            add_flathub_beta_repo_button.get_style_context().add_class("dark-install-button")
            add_flathub_beta_repo_button.connect("clicked", self.on_add_flathub_beta_repo_button_clicked)

            # Check for existing Flathub repositories and disable buttons accordingly
            flathub_url = "https://dl.flathub.org/repo/"
            flathub_beta_url = "https://dl.flathub.org/beta-repo/"

            existing_urls = [repo.get_url().rstrip('/') for repo in repos]
            add_flathub_repo_button.set_sensitive(flathub_url.rstrip('/') not in existing_urls)
            add_flathub_beta_repo_button.set_sensitive(flathub_beta_url.rstrip('/') not in existing_urls)

            # Add repositories to container
            for repo in repos:
                repo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                repo_box.set_spacing(6)
                repo_box.set_hexpand(True)

                # Create checkbox
                checkbox = Gtk.CheckButton(label=repo.get_name())
                checkbox.set_active(not repo.get_disabled())
                if not repo.get_disabled():
                    checkbox.get_style_context().remove_class("dim-label")
                else:
                    checkbox.get_style_context().add_class("dim-label")
                checkbox.connect("toggled", self.on_repo_toggled, repo)
                checkbox_url_label = Gtk.Label(label=repo.get_url())
                checkbox_url_label.set_halign(Gtk.Align.START)
                checkbox_url_label.set_hexpand(True)
                checkbox_url_label.get_style_context().add_class("dim-label")

                # Create delete button
                delete_button = Gtk.Button()
                delete_icon = Gio.Icon.new_for_string('list-remove')
                delete_button.set_image(Gtk.Image.new_from_gicon(delete_icon, Gtk.IconSize.BUTTON))
                delete_button.get_style_context().add_class("destructive-action")
                delete_button.connect("clicked", self.on_repo_delete, repo)

                # Add widgets to box
                repo_box.pack_start(checkbox, False, False, 0)
                repo_box.pack_start(checkbox_url_label, False, False, 0)
                repo_box.pack_end(delete_button, False, False, 0)

                # Add box to container
                repo_container.pack_start(repo_box, False, False, 0)

            repo_container.pack_start(add_repo_button, False, False, 0)
            repo_container.pack_start(add_flathub_repo_button, False, False, 0)
            repo_container.pack_start(add_flathub_beta_repo_button, False, False, 0)

            # Add container to scrolled window
            scrolled_window.add(repo_container)
            self.right_container.pack_start(scrolled_window, True, True, 0)

            self.right_container.show_all()
            return

        # Display each application
        for app in apps:
            details = app.get_details()
            is_installed = details['id'] in installed_package_ids
            is_updatable = details['id'] in updatable_package_ids

            # Create application container
            app_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            app_container.set_spacing(12)
            app_container.set_margin_top(6)
            app_container.set_margin_bottom(6)

            # Add icon placeholder
            icon_box = Gtk.Box()
            icon_box.set_size_request(94, -1)

            # Create and add the icon
            icon = Gtk.Image.new_from_file(f"{details['icon_path_128']}/{details['icon_filename']}")
            icon.set_size_request(74, 74)
            icon_box.pack_start(icon, True, True, 0)

            # Create right side layout for text
            right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            right_box.set_spacing(4)
            right_box.set_hexpand(True)

            # Add title
            title_label = Gtk.Label(label=details['name'])
            title_label.get_style_context().add_class("app-list-header")
            title_label.set_halign(Gtk.Align.START)
            title_label.set_valign(Gtk.Align.CENTER)
            title_label.set_hexpand(True)

            # Add summary
            desc_label = Gtk.Label(label=details['summary'])
            desc_label.set_halign(Gtk.Align.START)
            desc_label.set_valign(Gtk.Align.CENTER)
            desc_label.set_hexpand(True)
            desc_label.set_line_wrap(True)
            desc_label.set_line_wrap_mode(Gtk.WrapMode.WORD)
            desc_label.get_style_context().add_class("dim-label")

            # Create buttons box
            buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            buttons_box.set_spacing(6)
            buttons_box.set_margin_top(4)
            buttons_box.set_halign(Gtk.Align.END)

            # Install/Remove button
            if is_installed:
                button = self.create_button(
                    self.on_remove_clicked,
                    app,
                    None,
                    condition=lambda x: True
                )
                remove_icon = Gio.Icon.new_for_string('list-remove')
                button.set_image(Gtk.Image.new_from_gicon(remove_icon, Gtk.IconSize.BUTTON))
                button.get_style_context().add_class("dark-remove-button")
            else:
                button = self.create_button(
                    self.on_install_clicked,
                    app,
                    None,
                    condition=lambda x: True
                )
                install_icon = Gio.Icon.new_for_string('list-add')
                button.set_image(Gtk.Image.new_from_gicon(install_icon, Gtk.IconSize.BUTTON))
                button.get_style_context().add_class("dark-install-button")
            buttons_box.pack_end(button, False, False, 0)

            # Add Update button if available
            if is_updatable:
                update_button = self.create_button(
                    self.on_update_clicked,
                    app,
                    None,
                    condition=lambda x: True
                )
                update_icon = Gio.Icon.new_for_string('synchronize')
                update_button.set_image(Gtk.Image.new_from_gicon(update_icon, Gtk.IconSize.BUTTON))
                update_button.get_style_context().add_class("dark-install-button")
                buttons_box.pack_end(update_button, False, False, 0)

            # Details button
            details_btn = self.create_button(
                self.on_details_clicked,
                app,
                None
            )
            details_icon = Gio.Icon.new_for_string('question')
            details_btn.set_image(Gtk.Image.new_from_gicon(details_icon, Gtk.IconSize.BUTTON))
            details_btn.get_style_context().add_class("dark-install-button")
            buttons_box.pack_end(details_btn, False, False, 0)

            # Donate button with condition
            donate_btn = self.create_button(
                self.on_donate_clicked,
                app,
                None,
                condition=lambda x: x.get_details().get('urls', {}).get('donation', '')
            )
            if donate_btn:
                donate_icon = Gio.Icon.new_for_string('donate')
                donate_btn.set_image(Gtk.Image.new_from_gicon(donate_icon, Gtk.IconSize.BUTTON))
                donate_btn.get_style_context().add_class("dark-install-button")
                buttons_box.pack_end(donate_btn, False, False, 0)

            # Add widgets to right box
            right_box.pack_start(title_label, False, False, 0)
            right_box.pack_start(desc_label, False, False, 0)
            right_box.pack_start(buttons_box, False, True, 0)

            # Add separator
            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)

            # Add to container
            app_container.pack_start(icon_box, False, False, 0)
            app_container.pack_start(right_box, True, True, 0)
            self.right_container.pack_start(app_container, False, False, 0)
            self.right_container.pack_start(separator, False, False, 0)

        self.right_container.show_all()  # Show all widgets after adding them

    def on_install_clicked(self, button, app):
        """Handle the Install button click with installation options"""
        details = app.get_details()

        # Create dialog
        dialog = Gtk.Dialog(
            title=f"Install {details['name']}?",
            transient_for=self,
            modal=True,
            destroy_with_parent=True,
        )
        # Add buttons using the new method
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Install", Gtk.ResponseType.OK)

        # Create content area
        content_area = dialog.get_content_area()
        content_area.set_spacing(12)
        content_area.set_border_width(12)

        # Create repository dropdown
        repo_combo = Gtk.ComboBoxText()
        repo_combo.set_hexpand(True)

        content_area.pack_start(Gtk.Label(label=f"Install: {details['id']}?"), False, False, 0)

        # Search for available repositories containing this app
        searcher = libflatpak_query.get_reposearcher(self.system_mode)
        if self.system_mode is False:
            content_area.pack_start(Gtk.Label(label="Installation Type: User"), False, False, 0)
        else:
            content_area.pack_start(Gtk.Label(label="Installation Type: System"), False, False, 0)

        # Populate repository dropdown
        available_repos = set()
        repos = libflatpak_query.repolist(self.system_mode)
        for repo in repos:
            if not repo.get_disabled():
                search_results = searcher.search_flatpak(details['id'], repo.get_name())
                if search_results:
                    available_repos.add(repo)

        # Add repositories to dropdown
        if available_repos:
            repo_combo.remove_all()  # Clear any existing items

            # Add all repositories
            for repo in available_repos:
                repo_combo.append_text(repo.get_name())

            # Only show dropdown if there are multiple repositories
            if len(available_repos) >= 2:
                # Remove and re-add with dropdown visible
                content_area.pack_start(repo_combo, False, False, 0)
                repo_combo.set_button_sensitivity(Gtk.SensitivityType.AUTO)
                repo_combo.set_active(0)
            else:
                # Remove and re-add without dropdown
                content_area.remove(repo_combo)
                repo_combo.set_active(0)
        else:
            repo_combo.remove_all()  # Clear any existing items
            repo_combo.append_text("No repositories available")
            content_area.remove(repo_combo)

        # Show dialog
        dialog.show_all()

        # Run dialog
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            selected_repo = repo_combo.get_active_text()

            # Perform installation
            # Get selected values
            if self.system_mode is False:
                print(f"Installing {details['name']} for User from {selected_repo}")
            else:
                print(f"Installing {details['name']} for System from {selected_repo}")
            success, message = libflatpak_query.install_flatpak(app, selected_repo, self.system_mode)
            message_type=Gtk.MessageType.INFO
            if not success:
                message_type=Gtk.MessageType.ERROR
            if message:
                finished_dialog = Gtk.MessageDialog(
                    transient_for=self,
                    modal=True,
                    destroy_with_parent=True,
                    message_type=message_type,
                    buttons=Gtk.ButtonsType.OK,
                    text=message
                )
                self.refresh_local()
                finished_dialog.run()
                finished_dialog.destroy()

            self.refresh_current_page()
        dialog.destroy()

    def on_remove_clicked(self, button, app):
        """Handle the Remove button click with removal options"""
        details = app.get_details()

        # Create dialog
        dialog = Gtk.Dialog(
            title=f"Remove {details['name']}?",
            transient_for=self,
            modal=True,
            destroy_with_parent=True,
        )
        # Add buttons using the new method
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Remove", Gtk.ResponseType.OK)

        # Create content area
        content_area = dialog.get_content_area()
        content_area.set_spacing(12)
        content_area.set_border_width(12)

        content_area.pack_start(Gtk.Label(label=f"Remove: {details['id']}?"), False, False, 0)

        # Show dialog
        dialog.show_all()

        # Run dialog
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            # Perform Removal
            # Get selected values
            if self.system_mode is False:
                print(f"Removing {details['name']} for User.")
            else:
                print(f"Removing {details['name']} for System.")
            success, message = libflatpak_query.remove_flatpak(app, self.system_mode)
            message_type=Gtk.MessageType.INFO
            if not success:
                message_type=Gtk.MessageType.ERROR
            if message:
                finished_dialog = Gtk.MessageDialog(
                    transient_for=self,
                    modal=True,
                    destroy_with_parent=True,
                    message_type=message_type,
                    buttons=Gtk.ButtonsType.OK,
                    text=message
                )
                self.refresh_local()
                finished_dialog.run()
                finished_dialog.destroy()
            self.refresh_current_page()
        dialog.destroy()

    def on_update_clicked(self, button, app):
        """Handle the Update button click"""
        details = app.get_details()
        print(f"Updating application: {details['name']}")
        # Implement update logic here
        # Example:
        # Flatpak.update(app_id=details['id'])

    def on_details_clicked(self, button, app):
        """Handle the Details button click"""
        details = app.get_details()
        print(f"Showing details for: {details['name']}")
        # Implement details view here
        # Could open a new window with extended information

    def on_donate_clicked(self, button, app):
        """Handle the Donate button click"""
        details = app.get_details()
        donation_url = details.get('urls', {}).get('donation', '')
        if donation_url:
            try:
                Gio.AppInfo.launch_default_for_uri(donation_url, None)
            except Exception as e:
                print(f"Error opening donation URL: {str(e)}")

    def on_repo_toggled(self, checkbox, repo):
        """Handle repository enable/disable toggle"""
        repo.set_disabled(checkbox.get_active())
        # Update the UI to reflect the new state
        checkbox.get_parent().set_sensitive(True)
        if checkbox.get_active():
            checkbox.get_style_context().remove_class("dim-label")
            success, message = libflatpak_query.repotoggle(repo.get_name(), True, self.system_mode)
            message_type = Gtk.MessageType.INFO
            if success:
                self.refresh_local()
            else:
                if message:
                    message_type = Gtk.MessageType.ERROR
            if message:
                dialog = Gtk.MessageDialog(
                    transient_for=None,  # Changed from self
                    modal=True,
                    destroy_with_parent=True,
                    message_type=message_type,
                    buttons=Gtk.ButtonsType.OK,
                    text=message
                )
                dialog.run()
                dialog.destroy()
        else:
            checkbox.get_style_context().add_class("dim-label")
            success, message = libflatpak_query.repotoggle(repo.get_name(), False, self.system_mode)
            message_type = Gtk.MessageType.INFO
            if success:
                self.refresh_local()
            else:
                if message:
                    message_type = Gtk.MessageType.ERROR
            if message:
                dialog = Gtk.MessageDialog(
                    transient_for=None,  # Changed from self
                    modal=True,
                    destroy_with_parent=True,
                    message_type=message_type,
                    buttons=Gtk.ButtonsType.OK,
                    text=message
                )
                dialog.run()
                dialog.destroy()

    def on_repo_delete(self, button, repo):
        """Handle repository deletion"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            destroy_with_parent=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Are you sure you want to delete the '{repo.get_name()}' repository?"
        )

        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.YES:
            try:
                libflatpak_query.repodelete(repo.get_name(), self.system_mode)
                self.refresh_local()
                self.show_category_apps('repositories')
            except GLib.GError as e:
                # Handle polkit authentication failure
                if "not allowed for user" in str(e):
                    error_dialog = Gtk.MessageDialog(
                        transient_for=self,
                        modal=True,
                        destroy_with_parent=True,
                        message_type=Gtk.MessageType.ERROR,
                        buttons=Gtk.ButtonsType.OK,
                        text="You don't have permission to remove this repository. "
                            "Please try running the application with sudo privileges."
                    )
                    error_dialog.run()
                    error_dialog.destroy()
                else:
                    # Handle other potential errors
                    error_dialog = Gtk.MessageDialog(
                        transient_for=self,
                        modal=True,
                        destroy_with_parent=True,
                        message_type=Gtk.MessageType.ERROR,
                        buttons=Gtk.ButtonsType.OK,
                        text=f"Failed to remove repository: {str(e)}"
                    )
                    error_dialog.run()
                    error_dialog.destroy()

    def on_add_flathub_repo_button_clicked(self, button):
        """Handle the Add Flathub Repository button click"""
        # Add the repository
        success, error_message = libflatpak_query.repoadd("https://dl.flathub.org/repo/flathub.flatpakrepo", self.system_mode)
        if error_message:
            error_dialog = Gtk.MessageDialog(
                transient_for=None,  # Changed from self
                modal=True,
                destroy_with_parent=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=error_message
            )
            error_dialog.run()
            error_dialog.destroy()
        self.refresh_local()
        self.show_category_apps('repositories')

    def on_add_flathub_beta_repo_button_clicked(self, button):
        """Handle the Add Flathub Beta Repository button click"""
        # Add the repository
        success, error_message = libflatpak_query.repoadd("https://dl.flathub.org/beta-repo/flathub-beta.flatpakrepo", self.system_mode)
        if error_message:
            error_dialog = Gtk.MessageDialog(
                transient_for=None,  # Changed from self
                modal=True,
                destroy_with_parent=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=error_message
            )
            error_dialog.run()
            error_dialog.destroy()
        self.refresh_local()
        self.show_category_apps('repositories')

    def on_add_repo_button_clicked(self, button):
        """Handle the Add Repository button click"""
        # Create file chooser dialog
        dialog = Gtk.FileChooserDialog(
            title="Select Repository File",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
            flags=0
        )

        # Add buttons using the new method
        dialog.add_buttons(
            "Cancel", Gtk.ResponseType.CANCEL,
            "Open", Gtk.ResponseType.OK
        )

        # Add filter for .flatpakrepo files
        repo_filter = Gtk.FileFilter()
        repo_filter.set_name("Flatpak Repository Files")
        repo_filter.add_pattern("*.flatpakrepo")
        dialog.add_filter(repo_filter)

        # Show all files filter
        all_filter = Gtk.FileFilter()
        all_filter.set_name("All Files")
        all_filter.add_pattern("*")
        dialog.add_filter(all_filter)

        # Run the dialog
        response = dialog.run()
        repo_file_path = dialog.get_filename()
        dialog.destroy()

        if response == Gtk.ResponseType.OK and repo_file_path:
            # Add the repository
            success, error_message = libflatpak_query.repoadd(repo_file_path, self.system_mode)
            if error_message:
                error_dialog = Gtk.MessageDialog(
                    transient_for=None,  # Changed from self
                    modal=True,
                    destroy_with_parent=True,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text=error_message
                )
                error_dialog.run()
                error_dialog.destroy()
            self.refresh_local()
            self.show_category_apps('repositories')

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
