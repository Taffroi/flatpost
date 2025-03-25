![screenshot](screenshots/flatshop_agnostic.png)
![screenshot](screenshots/flatshop_agnostic2.png)


This is very much currently WIP.

DONE:
- Appstream metadata loading and search
- Appstream metadata refresh
- Collections metadata loading and search
- Collections metadata refresh
- Repository management functions
- Repository management GUI
- Installed package query functions
- Available updates package query functions
- GUI layout of system, collections, and categories entries.
- GUI layout of application list
- GUI layout of buttons
- GUI layout of search
- Donate/Support button and function.
- Install button functions
- Remove button functions
- System mode backend
- Search function

TODO:
- Update button functions
- Update management GUI
- System mode toggle
- Refresh metadata button
- List Applications only checkbox
- Package information page/section.
- Implement subcategories
- General GUI layout/theming improvements
- Sort runtimes from Desktop Apps


Usage (Temporary until proper packaging is added):

Shop: `./main.py`
CLI:
```
./libflatpak_query.py -h
usage: libflatpak_query.py [-h] [--id ID] [--repo REPO] [--list-all] [--categories] [--list-installed] [--check-updates] [--list-repos] [--add-repo REPO_FILE] [--remove-repo REPO_NAME] [--toggle-repo REPO_NAME ENABLE/DISABLE] [--install APP_ID] [--remove APP_ID] [--system]

Search Flatpak packages

options:
  -h, --help            show this help message and exit
  --id ID               Application ID to search for
  --repo REPO           Filter results to specific repository
  --list-all            List all available apps
  --categories          Show apps grouped by category
  --list-installed      List all installed Flatpak applications
  --check-updates       Check for available updates
  --list-repos          List all configured Flatpak repositories
  --add-repo REPO_FILE  Add a new repository from a .flatpakrepo file
  --remove-repo REPO_NAME
                        Remove a Flatpak repository
  --toggle-repo REPO_NAME ENABLE/DISABLE
                        Enable or disable a repository
  --install APP_ID      Install a Flatpak package
  --remove APP_ID       Remove a Flatpak package
  --system              Install as system instead of user

```

Common CLI combinations:
```
./libflatpak_query.py --id net.lutris.Lutris
./libflatpak_query.py --id net.lutris.Lutris --repo flatpak beta
./libflatpak_query.py --id net.lutris.Lutris --repo flatpak-beta --system
./libflatpak_query.py --list-all
./libflatpak_query.py --list-all --system
./libflatpak_query.py --categories
./libflatpak_query.py --categories --system
./libflatpak_query.py --list-installed
./libflatpak_query.py --list-installed --system
./libflatpak_query.py --check-updates
./libflatpak_query.py --check-updates --system
./libflatpak_query.py --list-repos
./libflatpak_query.py --list-repos --system
./libflatpak_query.py --add-repo <.flatpakrepo or url to .flatpakrepo file>
./libflatpak_query.py --add-repo <.flatpakrepo or url to .flatpakrepo file> --system
./libflatpak_query.py --remove-repo <repo name>
./libflatpak_query.py --remove-repo <repo name> --system
./libflatpak_query.py --toggle-repo <enable/disable> --repo <repo name>
./libflatpak_query.py --toggle-repo <enable/disable> --repo <repo name> --system
./libflatpak_query.py --install <app id>
./libflatpak_query.py --install <app id> --repo <repo name>
./libflatpak_query.py --install <app id> --repo <repo name> --system
./libflatpak_query.py --remove <app id>
./libflatpak_query.py --remove <app id> --system


```
