# yay-declare - Package State Manager

A Python utility for managing system packages on Arch Linux (and derivatives) by
synchronizing installed packages with configuration files.

## Overview

This tool compares the currently installed packages on your system against a set
of configuration files, then determines which packages need to be installed,
removed, or marked as dependencies. It supports dry-run mode for safe planning
and can automatically apply changes when desired.

### Features

- Declarative package management: Define your desired packages in text files
- Safe dry-run mode: Preview changes before applying them
- Group organization: Organize packages into different configuration files
- Ignore list: Specify packages that can remain installed even if not in configs
- Dependency marking: Specify packages to install as dependencies (--asdeps)
- Flexible filtering: Ignore files starting with _ and lines starting with #

## Requirements

- Arch Linux or derivative (e.g., Manjaro, EndeavourOS)
- Python 3
- [yay AUR helper](https://github.com/Jguer/yay)

## Installation

1. Clone or download the script to your desired location

2. Ensure the script is executable:

`chmod +x yay-declare.py`

## Usage

### Dry-run: Show what would be changed

`./yay-declare.py`

### Apply changes

`./yay-declare.py --apply` or `./yay-declare.py -a`

### Show help

`./yay-declare.py --help`

## Configuration Files

Place configuration files in the $HOME/.config/yay-declare directory:

- Package files: Regular text files (e.g., base, devel, gui)

- Ignore file: Named ignore (required for ignore functionality)

Package File Format Each line in a package file can be:

A package name: linux

A package name with --asdeps flag: libnotify --asdeps

A comment (starting with #): # This is a comment

Example (base file):

base:

```
linux
linux-headers
linux-firmware
libnotify --asdeps
# nvidia
```

### Ignore File Format

List packages that should never be removed, even if not present in your
configuration files:

ignore:

```
firefox
obs-studio
```

### File Naming Rules

Files starting with _ are ignored (e.g., _de will be skipped)

The ignore file is processed specially

Files with .sh, .py, .md extension are ignored

## How It Works

### Read Configuration

The script reads all package files (except those starting with _) and builds
sets of packages to install and mark as dependencies.

### Compare State

It compares the configured packages with currently installed packages (using yay
-Qe for explicitly installed and yay -Qd for dependencies).

### Generate Actions

The script determines:

- Packages to install (in config but not installed)
- Packages to remove (installed but not in config or ignore list)
- Packages to mark as dependencies (in config with --asdeps but not marked as
  such)

### Execute

When run with --apply or -a, it executes the necessary yay commands to
synchronize the system state.

## Example Workflow Create package configuration files:

echo "linux" > base\
echo "linux-headers" > base\
echo "libnotify --asdeps" > base\
echo "firefox" > gui

Create an ignore file if needed:\
echo "custom-tool" > ignore

## Preview changes:\

`./yay-declare.py`

Output: `yay -S firefox; yay -S --asdeps libnotify`

## Apply changes:

`./yay-declare.py --apply`

## Safety Notes

- Always review the dry-run output before applying changes
- The ignore file prevents removal of specified packages
- Files starting with _ won't be processed (useful for disabling groups)
- The script will not remove packages that are dependencies of other installed
  packages

## Limitations Requires

- yay specifically
- Designed for Arch Linux and derivatives
- Package files must be in the $HOME/.config/yay-declare directory as the script
- No version pinning or complex dependency resolution
- No changes detected: Ensure package files are in the correct directory and
  don't start with _

## Contributing

Feel free to modify the script for your specific needs. Common modifications
include:

Adding support for package versions

Implementing more complex filtering logic

License This is a utility script provided as-is. Use at your own risk.
