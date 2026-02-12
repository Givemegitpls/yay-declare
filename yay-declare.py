#!/usr/bin/python3
import os
import subprocess
import sys


class Expected:
    to_asdeps: set[str]
    to_install: set[str]
    to_remove: set[str]
    to_ignore: set[str]

    def __init__(
        self,
        to_asdeps: set[str] | None = None,
        to_install: set[str] | None = None,
        to_remove: set[str] | None = None,
        to_ignore: set[str] | None = None,
    ):
        self.to_asdeps = to_asdeps if to_asdeps else set()
        self.to_install = to_install if to_install else set()
        self.to_remove = to_remove if to_remove else set()
        self.to_ignore = to_ignore if to_ignore else set()


def gen_install_list(path: str) -> Expected:
    apps: list[str] = []
    deps: list[str] = []
    ignore: list[str] = []
    for root, _dirs, files in os.walk(path, followlinks=True):
        if root[1:] != "/":
            root = root + "/"
        for file in files:
            if file[0] in ["_", "."] or file[-3:] in [".sh", ".md", ".py"]:
                continue
            with open(f"{root}/{file}") as f:
                if file == "ignore":
                    for line in f:
                        line = line.replace("\n", "")
                        options = line.split(" ")
                        if len(options) > 1:
                            continue
                        ignore.append(line)
                    continue
                for line in f:
                    if "#" == line[:1]:
                        continue
                    line = line.replace("\n", "")
                    options = line.split(" ")
                    if len(options) > 2:
                        continue
                    elif "--asdeps" in line and len(options) > 1:
                        options.remove("--asdeps")
                        if options:
                            deps += options
                    else:
                        apps.append(line)

    return Expected(to_install=set(apps), to_asdeps=set(deps), to_ignore=set(ignore))


def gen_remove_list(expected: Expected) -> Expected:
    yay_explicit = subprocess.check_output(["yay", "-Qe"]).decode(sys.stdout.encoding)
    yay_deps = subprocess.check_output(["yay", "-Qd"]).decode(sys.stdout.encoding)
    installed_explicit: set[str] = set(
        [
            row.split(" ")[0]
            for row in yay_explicit.split("\n")
            if len(row.split(" ")) > 1
        ]
    )
    installed_deps: set[str] = set(
        [row.split(" ")[0] for row in yay_deps.split("\n") if len(row.split(" ")) > 1]
    )
    return Expected(
        to_remove=installed_explicit
        - expected.to_install
        - installed_deps
        - set(expected.to_ignore),
        to_install=expected.to_install - installed_explicit,
        to_asdeps=expected.to_asdeps - installed_deps,
    )


if __name__ == "__main__":
    service_name = "yay-declare"
    config_path = os.path.join(
        os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
        service_name,
    )
    expected = gen_install_list(config_path)
    needed = gen_remove_list(expected)
    query: list[str] = []
    if needed.to_remove:
        query.append("yay -Rns " + " ".join(needed.to_remove))
    if needed.to_install:
        query.append("yay -S " + " ".join(needed.to_install))
    if needed.to_asdeps:
        query.append("yay -S --asdeps " + " ".join(needed.to_asdeps))
    if len(sys.argv) == 2:
        arg = sys.argv[1]
        if arg in ["-a", "--apply"]:
            subprocess.call(";".join(query), shell=True)
        elif arg in ["-h", "--help"]:
            sys.stdout.write(
                'Usage: run scripts without arguments to dry-run\nUse -a, --apply to apply result\nAdd packages you want to ignore in "./ignore"\nAdd "_" as first char of file\'s name to disable group. For example: "de" >> "_de"'
            )
            sys.stdout.flush()
    else:
        sys.stdout.write(";".join(query))
        sys.stdout.flush()
