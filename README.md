![screenshot](screenshots/flatshop_agnostic.png)
![screenshot](screenshots/flatshop_agnostic2.png)


I wanted a desktop environment agnostic flatpak store that didn't require pulling in gnome or kde dependencies.

Built with python, gtk, libflatpak, appstream


All basic flatpak functionality implementation is done.

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
- System mode toggle
- Update button functions
- Implement subcategories
- Implement kind sorting in the installed/updates sections (desktop_app, addon, runtime, other..)
- Implement kind sorting dropdown for current page
- Implement kind sorting search filter
- Refresh metadata button
- Add install from .flatpakref functionality + drag and drop
- Add install from .flatpakrepo functionality + drag and drop
- Add per-app permission management backend
- Add global permission management backend
- Add per-app permission management GUI
- Add global permission management GUI
- Add Package information page/section.
- Cleanup permissions GUI
- Add permissions override viewing inside per-app permissions view.
- Add 'update all' functionality.
- add about section
- General GUI layout/theming improvements

TODO:
- Document fp_turbo functions

Usage (Temporary until proper packaging is added):

Shop: `./main.py`

CLI:
```
./fp_turbo.py -h
usage: fp_turbo.py [-h] [--id ID] [--repo REPO] [--list-all] [--categories] [--subcategories] [--list-installed] [--check-updates] [--list-repos] [--add-repo REPO_FILE] [--remove-repo REPO_NAME] [--toggle-repo ENABLE/DISABLE]
                           [--install APP_ID] [--remove APP_ID] [--update APP_ID] [--system] [--refresh] [--refresh-local] [--add-file-perms PATH] [--remove-file-perms PATH] [--list-file-perms] [--list-other-perm-toggles PERM_NAME]
                           [--toggle-other-perms ENABLE/DISABLE] [--perm-type PERM_TYPE] [--perm-option PERM_OPTION] [--list-other-perm-values PERM_NAME] [--add-other-perm-values TYPE] [--remove-other-perm-values TYPE] [--perm-value VALUE]
                           [--override] [--global-add-file-perms PATH] [--global-remove-file-perms PATH] [--global-list-file-perms] [--global-list-other-perm-toggles PERM_NAME] [--global-toggle-other-perms ENABLE/DISABLE]
                           [--global-list-other-perm-values PERM_NAME] [--global-add-other-perm-values TYPE] [--global-remove-other-perm-values TYPE] [--get-app-portal-permissions] [--get-portal-permissions TYPE] [--get-all-portal-permissions]
                           [--set-app-portal-permissions TYPE] [--portal-perm-value TYPE]

Search Flatpak packages

options:
  -h, --help            show this help message and exit
  --id ID               Application ID to search for
  --repo REPO           Filter results to specific repository
  --list-all            List all available apps
  --categories          Show apps grouped by category
  --subcategories       Show apps grouped by subcategory
  --list-installed      List all installed Flatpak applications
  --check-updates       Check for available updates
  --list-repos          List all configured Flatpak repositories
  --add-repo REPO_FILE  Add a new repository from a .flatpakrepo file
  --remove-repo REPO_NAME
                        Remove a Flatpak repository
  --toggle-repo ENABLE/DISABLE
                        Enable or disable a repository
  --install APP_ID      Install a Flatpak package
  --remove APP_ID       Remove a Flatpak package
  --update APP_ID       Update a Flatpak package
  --update-all          Apply all available updates
  --system              Install as system instead of user
  --refresh             Install as system instead of user
  --refresh-local       Install as system instead of user
  --add-file-perms PATH
                        Add file permissions to an app (e.g. any defaults: host, host-os, host-etc, home, or "/path/to/directory" for custom paths)
  --remove-file-perms PATH
                        Remove file permissions from an app (e.g. any defaults: host, host-os, host-etc, home, or "/path/to/directory" for custom paths)
  --list-file-perms     List configured file permissions for an app
  --list-other-perm-toggles PERM_NAME
                        List configured other permission toggles for an app (e.g. "shared", "sockets", "devices", "features", "persistent")
  --toggle-other-perms ENABLE/DISABLE
                        Toggle other permissions on/off (True/False)
  --perm-type PERM_TYPE
                        Type of permission to toggle (shared, sockets, devices, features)
  --perm-option PERM_OPTION
                        Specific permission option to toggle (e.g. network, ipc)
  --list-other-perm-values PERM_NAME
                        List configured other permission group values for an app (e.g. "environment", "session_bus", "system_bus")
  --add-other-perm-values TYPE
                        Add a permission value (e.g. "environment", "session_bus", "system_bus")
  --remove-other-perm-values TYPE
                        Remove a permission value (e.g. "environment", "session_bus", "system_bus")
  --perm-value VALUE    The complete permission value to add or remove (e.g. "XCURSOR_PATH=/run/host/user-share/icons:/run/host/share/icons")
  --override            Set global permission override instead of per-application
  --global-add-file-perms PATH
                        Add file permissions to an app (e.g. any defaults: host, host-os, host-etc, home, or "/path/to/directory" for custom paths)
  --global-remove-file-perms PATH
                        Remove file permissions from an app (e.g. any defaults: host, host-os, host-etc, home, or "/path/to/directory" for custom paths)
  --global-list-file-perms
                        List configured file permissions for an app
  --global-list-other-perm-toggles PERM_NAME
                        List configured other permission toggles for an app (e.g. "shared", "sockets", "devices", "features", "persistent")
  --global-toggle-other-perms ENABLE/DISABLE
                        Toggle other permissions on/off (True/False)
  --global-list-other-perm-values PERM_NAME
                        List configured other permission group values for an app (e.g. "environment", "session_bus", "system_bus")
  --global-add-other-perm-values TYPE
                        Add a permission value (e.g. "environment", "session_bus", "system_bus")
  --global-remove-other-perm-values TYPE
                        Remove a permission value (e.g. "environment", "session_bus", "system_bus")
  --get-app-portal-permissions
                        Check specified portal permissions (e.g. "background", "notifications", "microphone", "speakers", "camera", "location") for a specified application ID.
  --get-portal-permissions TYPE
                        List all current portal permissions for all applications
  --get-all-portal-permissions
                        List all current portal permissions for all applications
  --set-app-portal-permissions TYPE
                        Set specified portal permissions (e.g. "background", "notifications", "microphone", "speakers", "camera", "location") yes/no for a specified application ID.
  --portal-perm-value TYPE
                        Set specified portal permissions value (yes/no) for a specified application ID.
```

Common CLI combinations:
```
./fp_turbo.py --id <app id>
./fp_turbo.py --id <app id> --repo flatpak beta
./fp_turbo.py --id <app id> --repo flatpak-beta --system
./fp_turbo.py --list-all
./fp_turbo.py --list-all --system
./fp_turbo.py --categories
./fp_turbo.py --categories --system
./fp_turbo.py --subcategories
./fp_turbo.py --subcategories --system
./fp_turbo.py --list-installed
./fp_turbo.py --list-installed --system
./fp_turbo.py --check-updates
./fp_turbo.py --check-updates --system
./fp_turbo.py --list-repos
./fp_turbo.py --list-repos --system
./fp_turbo.py --add-repo <.flatpakrepo or url to .flatpakrepo file>
./fp_turbo.py --add-repo <.flatpakrepo or url to .flatpakrepo file> --system
./fp_turbo.py --remove-repo <repo name>
./fp_turbo.py --remove-repo <repo name> --system
./fp_turbo.py --toggle-repo <enable/disable> --repo <repo name>
./fp_turbo.py --toggle-repo <enable/disable> --repo <repo name> --system
./fp_turbo.py --install <app id>
./fp_turbo.py --install <app id> --repo <repo name>
./fp_turbo.py --install <app id> --repo <repo name> --system
./fp_turbo.py --remove <app id>
./fp_turbo.py --remove <app id> --system
./fp_turbo.py --update <app id>
./fp_turbo.py --update <app id> --system
./fp_turbo.py --update-all
./fp_turbo.py --update-all --system
./fp_turbo.py --id <app id> --list-file-perms
./fp_turbo.py --id <app id> --add-file-perms <host, host-os, host-etc, home, or "/path/to/directory" for custom paths>
./fp_turbo.py --id <app id> --remove-file-perms <host, host-os, host-etc, home, or "/path/to/directory" for custom paths>
./fp_turbo.py --id <app id> --list-other-perm-toggles <shared, sockets, devices, features, persistent>
./fp_turbo.py --id <app id> --toggle-other-perms True --perm-type <shared, sockets, devices, features, persistent> --perm-option <network, ipc>
./fp_turbo.py --id <app id> --toggle-other-perms False --perm-type <shared, sockets, devices, features, persistent> --perm-option <network, ipc>
./fp_turbo.py --id <app id> --list-other-perm-values <environment, session_bus, system_bus>
./fp_turbo.py --id <app id> --add-other-perm-values <environment, session_bus, system_bus> --perm-value <ENVVAR=value or xxx.yyy.zzz=talk or xxx.yyy.zzz=own>
./fp_turbo.py --id <app id> --remove-other-perm-values <environment, session_bus, system_bus> --perm-value <ENVVAR=value or xxx.yyy.zzz=talk or xxx.yyy.zzz=own>
./fp_turbo.py --override --global-list-file-perms
./fp_turbo.py --override --global-add-file-perms <host, host-os, host-etc, home, or "/path/to/directory" for custom paths>
./fp_turbo.py --override --global-remove-file-perms <host, host-os, host-etc, home, or "/path/to/directory" for custom paths>
./fp_turbo.py --override --global-list-other-perm-toggles <shared, sockets, devices, features, persistent>
./fp_turbo.py --override --global-toggle-other-perms True --perm-type <shared, sockets, devices, features, persistent> --perm-option <network, ipc>
./fp_turbo.py --override --global-toggle-other-perms False --perm-type <shared, sockets, devices, features, persistent> --perm-option <network, ipc>
./fp_turbo.py --override --global-list-other-perm-values <environment, session_bus, system_bus>
./fp_turbo.py --override --global-add-other-perm-values <environment, session_bus, system_bus> --perm-value <ENVVAR=value or xxx.yyy.zzz=talk or xxx.yyy.zzz=own>
./fp_turbo.py --override --global-remove-other-perm-values <environment, session_bus, system_bus> --perm-value <ENVVAR=value or xxx.yyy.zzz=talk or xxx.yyy.zzz=own>
./fp_turbo.py --id <app id> --list-file-perms --system
./fp_turbo.py --id <app id> --add-file-perms <host, host-os, host-etc, home, or "/path/to/directory" for custom paths> --system
./fp_turbo.py --id <app id> --remove-file-perms <host, host-os, host-etc, home, or "/path/to/directory" for custom paths> --system
./fp_turbo.py --id <app id> --add-file-perms "/path/to/directory" --perm-type persistent
./fp_turbo.py --id <app id> --remove-file-perms "/path/to/directory" --perm-type persistent
./fp_turbo.py --id <app id> --list-other-perm-toggles <shared, sockets, devices, features, persistent> --system
./fp_turbo.py --id <app id> --toggle-other-perms True --perm-type <shared, sockets, devices, features, persistent> --perm-option <network, ipc> --system
./fp_turbo.py --id <app id> --toggle-other-perms False --perm-type <shared, sockets, devices, features, persistent> --perm-option <network, ipc> --system
./fp_turbo.py --id <app id> --list-other-perm-values <environment, session_bus, system_bus> --system
./fp_turbo.py --id <app id> --add-other-perm-values <environment, session_bus, system_bus> --perm-value <ENVVAR=value or xxx.yyy.zzz=talk or xxx.yyy.zzz=own> --system
./fp_turbo.py --id <app id> --remove-other-perm-values <environment, session_bus, system_bus> --perm-value <ENVVAR=value or xxx.yyy.zzz=talk or xxx.yyy.zzz=own> --system
./fp_turbo.py --override --global-list-file-perms --system
./fp_turbo.py --override --global-add-file-perms <host, host-os, host-etc, home, or "/path/to/directory" for custom paths> --system
./fp_turbo.py --override --global-remove-file-perms <host, host-os, host-etc, home, or "/path/to/directory" for custom paths> --system
./fp_turbo.py --override --global-list-other-perm-toggles <shared, sockets, devices, features, persistent> --system
./fp_turbo.py --override --global-toggle-other-perms True --perm-type <shared, sockets, devices, features, persistent> --perm-option <network, ipc> --system
./fp_turbo.py --override --global-toggle-other-perms False --perm-type <shared, sockets, devices, features, persistent> --perm-option <network, ipc> --system
./fp_turbo.py --override --global-list-other-perm-values <environment, session_bus, system_bus> --system
./fp_turbo.py --override --global-add-other-perm-values <environment, session_bus, system_bus> --perm-value <ENVVAR=value or xxx.yyy.zzz=talk or xxx.yyy.zzz=own> --system
./fp_turbo.py --override --global-remove-other-perm-values <environment, session_bus, system_bus> --perm-value <ENVVAR=value or xxx.yyy.zzz=talk or xxx.yyy.zzz=own> --system
./fp_turbo.py --get-all-portal-permissions
./fp_turbo.py --get-portal-permissions <portal>
./fp_turbo.py --get-app-portal-permissions --id <app id>
./fp_turbo.py --set-app-portal-permissions <portal> --portal-perm-value <yes/no> --id <app id>
```
