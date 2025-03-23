#!/usr/bin/env python3
import gi
gi.require_version("AppStream", "1.0")
gi.require_version("Flatpak", "1.0")

from gi.repository import Flatpak, GLib, Gio, AppStream
from pathlib import Path
import logging
from enum import IntEnum
import argparse

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
    def version(self) -> str:
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


    def get_all_apps(self, repo_name: str = None) -> list[AppStreamPackage]:
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

    args = parser.parse_args()
    app_id = args.id
    repo_filter = args.repo
    list_all = args.list_all
    show_categories = args.categories

    # Create AppstreamSearcher instance
    searcher = AppstreamSearcher()

    # Add installations
    installation = Flatpak.Installation.new_system(None)
    searcher.add_installation(installation)

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
