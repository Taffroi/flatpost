#!/usr/bin/env python3
import gi
gi.require_version("AppStream", "1.0")
gi.require_version("Flatpak", "1.0")

from gi.repository import Flatpak, GLib, Gio, AppStream
from pathlib import Path
import logging
from enum import IntEnum
import argparse
import requests
from urllib.parse import quote_plus
import tempfile
import os
import sys
import json
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Match(IntEnum):
    NAME = 1
    ID = 2
    SUMMARY = 3
    NONE = 4


class AppStreamPackage:
    def __init__(self, comp: AppStream.Component, remote: Flatpak.Remote) -> None:
        self.component: AppStream.Component = comp
        self.remote: Flatpak.Remote = remote
        self.repo_name: str = remote.get_name()
        bundle: AppStream.Bundle = comp.get_bundle(AppStream.BundleKind.FLATPAK)
        self.flatpak_bundle: str = bundle.get_id()
        self.match = Match.NONE

        # Get icon and description
        self.icon_url = self._get_icon_url()
        self.icon_path_128 = self._get_icon_cache_path("128x128")
        self.icon_path_64 = self._get_icon_cache_path("64x64")
        self.icon_filename = self._get_icon_filename()
        self.description = self.component.get_description()

        # Get URLs from the component
        self.urls = self._get_urls()

        self.developer = self.component.get_developer().get_name()
        self.categories = self._get_categories()

    @property
    def id(self) -> str:
        return self.component.get_id()

    @property
    def name(self) -> str:
        return self.component.get_name()

    @property
    def summary(self) -> str:
        return self.component.get_summary()

    @property
    def version(self) -> str|None:
        releases = self.component.get_releases_plain()
        if releases:
            release = releases.index_safe(0)
            if release:
                version = release.get_version()
                return version
        return None

    def _get_icon_url(self) -> str:
        """Get the remote icon URL from the component"""
        icons = self.component.get_icons()

        # Find the first REMOTE icon
        remote_icon = next((icon for icon in icons if icon.get_kind() == AppStream.IconKind.REMOTE), None)
        return remote_icon.get_url() if remote_icon else ""

    def _get_icon_filename(self) -> str:
        """Get the cached icon filename from the component"""
        icons = self.component.get_icons()

        # Find the first CACHED icon
        cached_icon = next((icon for icon in icons if icon.get_kind() == AppStream.IconKind.CACHED), None)
        return cached_icon.get_filename() if cached_icon else ""

    def _get_icon_cache_path(self, size: str) -> str:

        # Appstream icon cache path for the flatpak repo queried
        icon_cache_path = Path(self.remote.get_appstream_dir().get_path() + "/icons/flatpak/" + size + "/")
        return str(icon_cache_path)

    def _get_urls(self) -> dict:
        """Get URLs from the component"""
        urls = {
            'donation': self._get_url('donation'),
            'homepage': self._get_url('homepage'),
            'bugtracker': self._get_url('bugtracker')
        }
        return urls

    def _get_url(self, url_kind: str) -> str:
        """Helper method to get a specific URL type"""
        # Convert string to AppStream.UrlKind enum
        url_kind_enum = getattr(AppStream.UrlKind, url_kind.upper())
        url = self.component.get_url(url_kind_enum)
        if url:
            return url
        return ""

    def _get_categories(self) -> list:
        categories_fetch = self.component.get_categories()
        categories = []
        for category in categories_fetch:
            categories.append(category.lower())
        return categories

    def search(self, keyword: str) -> Match:
        """Search for keyword in package details"""
        if keyword in self.name.lower():
            return Match.NAME
        elif keyword in self.id.lower():
            return Match.ID
        elif keyword in self.summary.lower():
            return Match.SUMMARY
        else:
            return Match.NONE

    def __str__(self) -> str:
        return f"{self.name} - {self.summary} ({self.flatpak_bundle})"

    def get_details(self) -> dict:
        """Get all package details including icon and description"""
        return {
            "name": self.name,
            "id": self.id,
            "summary": self.summary,
            "description": self.description,
            "version": self.version,
            "icon_url": self.icon_url,
            "icon_path_128": self.icon_path_128,
            "icon_path_64": self.icon_path_64,
            "icon_filename": self.icon_filename,
            "urls": self.urls,
            "developer": self.developer,
            #"architectures": self.architectures,
            "categories": self.categories,
            "bundle_id": self.flatpak_bundle,
            "match_type": self.match.name,
            "repo": self.repo_name
        }

class AppstreamSearcher:
    """Flatpak AppStream Package seacher"""

    def __init__(self) -> None:
        self.remotes: dict[str, list[AppStreamPackage]] = {}
        self.installed = []
        self.refresh_progress = 0

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

    def add_installation(self, inst: Flatpak.Installation):
        """Add enabled flatpak repositories from Flatpak.Installation"""
        remotes = inst.list_remotes()
        for remote in remotes:
            if not remote.get_disabled():
                self.add_remote(remote, inst)

    def add_remote(self, remote: Flatpak.Remote, inst: Flatpak.Installation):
        """Add packages for a given Flatpak.Remote"""
        remote_name = remote.get_name()
        self.installed.extend([ref.format_ref() for ref in inst.list_installed_refs_by_kind(Flatpak.RefKind.APP)])
        if remote_name not in self.remotes:
            self.remotes[remote_name] = self._load_appstream_metadata(remote)

    def _load_appstream_metadata(self, remote: Flatpak.Remote) -> list[AppStreamPackage]:
        """load AppStrean metadata and create AppStreamPackage objects"""
        packages = []
        metadata = AppStream.Metadata.new()
        metadata.set_format_style(AppStream.FormatStyle.CATALOG)
        appstream_file = Path(remote.get_appstream_dir().get_path() + "/appstream.xml.gz")
        if appstream_file.exists():
            metadata.parse_file(Gio.File.new_for_path(appstream_file.as_posix()), AppStream.FormatKind.XML)
            components: AppStream.ComponentBox = metadata.get_components()
            i = 0
            for i in range(components.get_size()):
                component = components.index_safe(i)
                if component.get_kind() == AppStream.ComponentKind.DESKTOP_APP:
                    bundle = component.get_bundle(AppStream.BundleKind.FLATPAK).get_id()
                    if bundle not in self.installed:
                        packages.append(AppStreamPackage(component, remote))
            return packages
        else:
            logger.debug(f"AppStream file not found: {appstream_file}")
            return []

    def search_flatpak_repo(self, keyword: str, repo_name: str) -> list[AppStreamPackage]:
        search_results = []
        packages = self.remotes[repo_name]
        for package in packages:
            # Try matching exact ID first
            if keyword is package.id:
                search_results.append(package)
            # Try matching case insensitive ID next
            elif keyword.lower() is package.id.lower():
                search_results.append(package)
            # General keyword search
            elif keyword.lower() in str(package).lower():
                search_results.append(package)
        return search_results


    def search_flatpak(self, keyword: str, repo_name=None) -> list[AppStreamPackage]:
        """Search packages matching a keyword"""
        search_results = []
        keyword = keyword
        if repo_name and repo_name in self.remotes.keys():
            results = self.search_flatpak_repo(keyword, repo_name)
            for result in results:
                search_results.append(result)
            return search_results
        for remote_name in self.remotes.keys():
            results = self.search_flatpak_repo(keyword, remote_name)
            for result in results:
                search_results.append(result)
        return search_results


    def get_all_apps(self, repo_name=None) -> list[AppStreamPackage]:
        """Get all available apps from specified or all repositories"""
        all_packages = []
        if repo_name:
            if repo_name in self.remotes:
                all_packages = self.remotes[repo_name]
        else:
            for remote_name in self.remotes.keys():
                all_packages.extend(self.remotes[remote_name])
        return all_packages

    def get_categories_summary(self, repo_name: str = None) -> dict:
        """Get a summary of all apps grouped by category"""
        apps = self.get_all_apps(repo_name)
        categories = {}

        for app in apps:
            for category in app.categories:
                if category not in categories:
                    categories[category] = []
                categories[category].append(app)

        return categories

    def get_installed_apps(self) -> list[tuple[str, str, str]]:
        """Get a list of all installed Flatpak applications with their repository source"""
        installed_refs = []

        # Get both system-wide and user installations
        system_inst = Flatpak.Installation.new_system(None)
        user_inst = Flatpak.Installation.new_user(None)

        def process_installed_refs(inst: Flatpak.Installation, repo_type: str):
            for ref in inst.list_installed_refs_by_kind(Flatpak.RefKind.APP):
                app_id = ref.format_ref()

                # Get remote name from the installation
                remote_name = ref.get_origin()
                # Handle cases where remote might be None
                if not remote_name:
                    remote_name = repo_type.capitalize()

                installed_refs.append((app_id, remote_name, repo_type))

        # Process both system-wide and user installations
        process_installed_refs(system_inst, "system")
        process_installed_refs(user_inst, "user")

        # Remove duplicates while maintaining order
        seen = set()
        unique_installed = [(ref, repo, repo_type) for ref, repo, repo_type in installed_refs
                        if not (ref in seen or seen.add(ref))]

        return unique_installed

    def check_updates(self) -> list[tuple[str, str, str]]:
        """Check for available updates for installed Flatpak applications"""
        updates = []

        # Get both system-wide and user installations
        system_inst = Flatpak.Installation.new_system(None)
        user_inst = Flatpak.Installation.new_user(None)

        def check_updates_for_install(inst: Flatpak.Installation, repo_type: str):
            for ref in inst.list_installed_refs_for_update(None):
                app_id = ref.get_name()

                # Get remote name from the installation
                remote_name = ref.get_origin()
                # Handle cases where remote might be None
                if not remote_name:
                    remote_name = repo_type.capitalize()

                updates.append((remote_name, app_id, repo_type))

        # Check system-wide installation
        check_updates_for_install(system_inst, "system")

        # Check user installation
        check_updates_for_install(user_inst, "user")

        return updates

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
                data = response.json()

                # If this is a collections category, save it to our collections database
                if category in self.category_groups['collections']:
                    if not hasattr(self, 'collections_db'):
                        self.collections_db = []
                    self.collections_db.append({
                        'category': category,
                        'data': data
                    })

                return data
            else:
                print(f"Failed to fetch apps: Status code {response.status_code}")
                return None
        except requests.RequestException as e:
            print(f"Error fetching apps: {str(e)}")
            return None

    def save_collections_data(self, filename='collections_data.json'):
        """Save all collected collections data to a JSON file."""
        if not hasattr(self, 'collections_db') or not self.collections_db:
            return

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.collections_db, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving collections data: {str(e)}")

    def update_collection_results(self, new_collection_results):
        """Update search results by replacing existing items and adding new ones."""
        # Create a set of existing app_ids for efficient lookup
        existing_app_ids = {app.id for app in self.collection_results}

        # Create a list to store the updated results
        updated_results = []

        # First add all existing results
        updated_results.extend(self.collection_results)

        # Add new results, replacing any existing ones
        for new_result in new_collection_results:
            app_id = new_result.id
            if app_id in existing_app_ids:
                # Replace existing result
                for i, existing in enumerate(updated_results):
                    if existing.id == app_id:
                        updated_results[i] = new_result
                        break
            else:
                # Add new result
                updated_results.append(new_result)

        self.collection_results = updated_results

    def refresh_data(self):

        # make sure to reset these to empty before refreshing.
        self.category_results = []  # Initialize empty list
        self.collection_results = []  # Initialize empty list
        self.installed_results = []  # Initialize empty list
        self.updates_results = []  # Initialize empty list

        total_categories = sum(len(categories) for categories in self.category_groups.values())
        current_category = 0

        # Search for each app in local repositories
        searcher = get_reposearcher()

        json_path = "collections_data.json"
        search_result = []
        for group_name, categories in self.category_groups.items():
            # Process categories one at a time to keep GUI responsive
            for category, title in categories.items():
                if category not in self.category_groups['system']:
                    # Preload the currently saved collections data first
                    try:
                        with open(json_path, 'r', encoding='utf-8') as f:
                            collections_data = json.load(f)
                            for collection in collections_data:
                                if collection['category'] == category:
                                    apps =  [app['app_id'] for app in collection['data'].get('hits', [])]
                                    for app_id in apps:
                                        search_result = searcher.search_flatpak(app_id, 'flathub')
                                        self.collection_results.extend(search_result)
                    except (IOError, json.JSONDecodeError) as e:
                        print(f"Error loading collections data: {str(e)}")

                    # Try to get apps from Flathub API if internet is available
                    if check_internet():
                        # Get modification time in seconds since epoch
                        mod_time = os.path.getmtime(json_path)
                        # Calculate 24 hours in seconds
                        hours_24 = 24 * 3600
                        # Check if file is older than 24 hours
                        if (time.time() - mod_time) > hours_24:
                            api_data = self.fetch_flathub_category_apps(category)
                            if api_data:
                                apps = api_data['hits']

                                for app in apps:
                                    app_id = app['app_id']
                                    # Search for the app in local repositories
                                    search_result = searcher.search_flatpak(app_id, 'flathub')
                                    self.category_results.extend(search_result)
                    else:
                        apps = searcher.get_all_apps('flathub')
                        for app in apps:
                            details = app.get_details()
                            if category in details['categories']:
                                search_result = searcher.search_flatpak(details['name'], 'flathub')
                                self.category_results.extend(search_result)

                    current_category += 1

                    # Update progress bar
                    self.refresh_progress = (current_category / total_categories) * 100

                else:
                    if "installed" in category:
                        installed_apps = searcher.get_installed_apps()
                        for app_id, repo_name, repo_type in installed_apps:
                            parts = app_id.split('/')
                            app_id = parts[parts.index('app') + 1]
                            if repo_name:
                                # Extend the existing list instead of creating a new one
                                search_result = searcher.search_flatpak(app_id, repo_name)
                                self.installed_results.extend(search_result)
                    elif "updates" in category:
                        updates = searcher.check_updates()
                        for repo_name, app_id, repo_type in updates:
                            if repo_name:
                                search_result = searcher.search_flatpak(app_id, repo_name)
                                self.updates_results.extend(search_result)
        self.save_collections_data()

        # load collections from json file again
        # we do this in one go after all of the data from each category has been saved to the json file.
        # this time we update entries that already exist and add new entries that don't exist.
        for group_name, categories in self.category_groups.items():
            for category, title in categories.items():
                if category in self.category_groups['collections']:
                    try:
                        with open(json_path, 'r', encoding='utf-8') as f:
                            collections_data = json.load(f)
                            for collection in collections_data:
                                if collection['category'] == category:
                                    apps =  [app['app_id'] for app in collection['data'].get('hits', [])]
                                    new_results = []
                                    for app_id in apps:
                                        search_result = searcher.search_flatpak(app_id, 'flathub')
                                        new_results.extend(search_result)
                                    self.update_collection_results(new_results)
                    except (IOError, json.JSONDecodeError) as e:
                        print(f"Error loading collections data: {str(e)}")
        # make sure to reset these to empty before refreshing.
        return self.category_results, self.collection_results, self.installed_results, self.updates_results

def get_refresh_progress():
    searcher = AppstreamSearcher()
    searcher.add_installation(Flatpak.Installation.new_system())
    return searcher

def get_reposearcher():
    searcher = AppstreamSearcher()
    searcher.add_installation(Flatpak.Installation.new_system())
    return searcher

def check_internet():
    """Check if internet connection is available."""
    try:
        requests.head('https://flathub.org', timeout=3)
        return True
    except requests.ConnectionError:
        return False

def repotoggle(repo, bool=True):
    """
    Enable or disable a Flatpak repository

    Args:
        repo (str): Name of the repository to toggle
        enable (bool): True to enable, False to disable

    Returns:
        tuple: (success, error_message)
    """
    installation = Flatpak.Installation.new_system()

    try:
        remote = installation.get_remote_by_name(repo)
        if not remote:
            return False, f"Repository '{repo}' not found."

        remote.set_disabled(not bool)

       # Modify the remote's disabled status
        success = installation.modify_remote(
            remote,
            None
        )
        if success:
            if bool:
                message = f"Successfully enabled {repo}."
            else:
                message = f"Successfully disabled {repo}."
            return True, message

    except GLib.GError as e:
        return False, f"Failed to toggle repository: {str(e)}."

def repolist():
    installation = Flatpak.Installation.new_system()
    repos = installation.list_remotes()
    return repos

def repodelete(repo):
    installation = Flatpak.Installation.new_system()
    installation.remove_remote(repo)

def repoadd(repofile):
    """Add a new repository using a .flatpakrepo file"""
    # Get existing repositories
    installation = Flatpak.Installation.new_system()
    existing_repos = installation.list_remotes()

    if not repofile.endswith('.flatpakrepo'):
        return False, "Repository file path or URL must end with .flatpakrepo extension."
    if repofile_is_url(repofile):
        try:
            local_path = download_repo(repofile)
            repofile = local_path
        except:
            return False, f"Repository file '{repofile}' could not be downloaded."
    if not os.path.exists(repofile):
        return False, f"Repository file '{repofile}' does not exist."

    # Get repository title from file name
    title = os.path.basename(repofile).replace('.flatpakrepo', '')

    # Check for duplicate title (case insensitive)
    existing_titles = [repo.get_name().casefold() for repo in existing_repos]

    if title.casefold() in existing_titles:
        return False, "A repository with this title already exists."

    # Read the repository file
    try:
        with open(repofile, 'rb') as f:
            repo_data = f.read()
    except IOError as e:
        return False, f"Failed to read repository file: {str(e)}"

    # Convert the data to GLib.Bytes
    repo_bytes = GLib.Bytes.new(repo_data)

    # Create a new remote from the repository file
    try:
        remote = Flatpak.Remote.new_from_file(title, repo_bytes)

        # Get URLs and normalize them by removing trailing slashes
        new_url = remote.get_url().rstrip('/')
        existing_urls = [repo.get_url().rstrip('/') for repo in existing_repos]

        # Check if URL already exists
        if new_url in existing_urls:
            return False, f"A repository with URL '{new_url}' already exists."

        installation.add_remote(remote, True, None)
    except GLib.GError as e:
        return False, f"Failed to add repository: {str(e)}"
    return True, None

def repofile_is_url(string):
    """Check if a string is a valid URL"""
    try:
        result = urllib.parse.urlparse(string)
        return all([result.scheme, result.netloc])
    except:
        return False

def download_repo(url):
    """Download a repository file from URL to /tmp/"""
    try:
        # Create a deterministic filename based on the URL
        url_path = urllib.parse.urlparse(url).path
        filename = os.path.basename(url_path) or 'repo'
        tmp_path = Path(tempfile.gettempdir()) / f"{filename}.flatpakrepo"

        # Download the file
        with requests.get(url, stream=True) as response:
            response.raise_for_status()

            # Write the file in chunks, overwriting if it exists
            with open(tmp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

        return str(tmp_path)
    except requests.RequestException as e:
        raise argparse.ArgumentTypeError(f"Failed to download repository file: {str(e)}")
    except IOError as e:
        raise argparse.ArgumentTypeError(f"Failed to save repository file: {str(e)}")


def main():
    """Main function demonstrating Flatpak information retrieval"""

    parser = argparse.ArgumentParser(description='Search Flatpak packages')
    parser.add_argument('--id', help='Application ID to search for')
    parser.add_argument('--repo', help='Filter results to specific repository')
    parser.add_argument('--list-all', action='store_true', help='List all available apps')
    parser.add_argument('--categories', action='store_true', help='Show apps grouped by category')
    parser.add_argument('--list-installed', action='store_true',
                       help='List all installed Flatpak applications')
    parser.add_argument('--check-updates', action='store_true',
                       help='Check for available updates')
    parser.add_argument('--list-repos', action='store_true',
                       help='List all configured Flatpak repositories')
    parser.add_argument('--add-repo', type=str, metavar='REPO_FILE',
                       help='Add a new repository from a .flatpakrepo file')
    parser.add_argument('--remove-repo', type=str, metavar='REPO_NAME',
                       help='Remove a Flatpak repository')
    parser.add_argument('--toggle-repo', type=str, nargs=2,
                       metavar=('REPO_NAME', 'ENABLE/DISABLE'),
                       help='Enable or disable a repository')

    args = parser.parse_args()
    app_id = args.id
    repo_filter = args.repo
    list_all = args.list_all
    show_categories = args.categories

    # Repository management operations
    if args.toggle_repo:
        repo_name, enable_str = args.toggle_repo
        if enable_str.lower() not in ['true', 'false', 'enable', 'disable']:
            print("Invalid enable/disable value. Use 'true/false' or 'enable/disable'")
            sys.exit(1)

        enable = enable_str.lower() in ['true', 'enable']
        success, message = repotoggle(repo_name, enable)
        print(message)
        sys.exit(0 if success else 1)

    if args.list_repos:
        repos = repolist()
        print("\nConfigured Repositories:")
        for repo in repos:
            print(f"- {repo.get_name()} ({repo.get_url()})")
        return

    if args.add_repo:
        success, error_message = repoadd(args.add_repo)
        if error_message:
            print(error_message)
            sys.exit(1)
        else:
            print(f"\nRepository added successfully: {args.add_repo}")
        return

    if args.remove_repo:
        repodelete(args.remove_repo)
        print(f"\nRepository removed successfully: {args.remove_repo}")
        return

    # Create AppstreamSearcher instance
    searcher = get_reposearcher()

    if args.list_installed:
        installed_apps = searcher.get_installed_apps()
        print(f"\nInstalled Flatpak Applications ({len(installed_apps)}):")
        for app_id, repo_name, repo_type in installed_apps:
            parts = app_id.split('/')
            app_id = parts[parts.index('app') + 1]
            print(f"{app_id} (Repository: {repo_name}, Installation: {repo_type})")
        return

    if args.check_updates:
        updates = searcher.check_updates()
        print(f"\nAvailable Updates ({len(updates)}):")
        for repo_name, app_id, repo_type in updates:
            print(f"{app_id} (Repository: {repo_name}, Installation: {repo_type})")
        return

    if list_all:
        apps = searcher.get_all_apps(repo_filter)
        for app in apps:
            details = app.get_details()
            print(f"Name: {details['name']}")
            print(f"Categories: {', '.join(details['categories'])}")
            print("-" * 50)
        return

    if show_categories:
        categories = searcher.get_categories_summary(repo_filter)
        for category, apps in categories.items():
            print(f"\n{category.upper()}:")
            for app in apps:
                print(f"  - {app.name} ({app.id})")
        return

    if app_id == "" or len(app_id) < 3:
        self._clear()
        return

    logger.debug(f"(flatpak_search) key: {app_id}")

    # Now you can call search method on the searcher instance
    if repo_filter:
        search_results = searcher.search_flatpak(app_id, repo_filter)
    else:
        search_results = searcher.search_flatpak(app_id)
    if search_results:
        for package in search_results:
            details = package.get_details()
            print(f"Name: {details['name']}")
            print(f"ID: {details['id']}")
            print(f"Summary: {details['summary']}")
            print(f"Description: {details['description']}")
            print(f"Version: {details['version']}")
            print(f"Icon URL: {details['icon_url']}")
            print(f"Icon PATH 128x128: {details['icon_path_128']}")
            print(f"Icon PATH 64x64: {details['icon_path_64']}")
            print(f"Icon FILE: {details['icon_filename']}")
            print(f"Developer: {details['developer']}")
            print(f"Categories: {details['categories']}")

            urls = details['urls']
            print(f"Donation URL: {urls['donation']}")
            print(f"Homepage URL: {urls['homepage']}")
            print(f"Bug Tracker URL: {urls['bugtracker']}")

            print(f"Bundle ID: {details['bundle_id']}")
            print(f"Match Type: {details['match_type']}")
            print(f"Repo: {details['repo']}")
            print("-" * 50)
    return

if __name__ == "__main__":
    main()
