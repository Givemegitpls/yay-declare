#!/usr/bin/python3
import os
import subprocess
import sys


class Expected:
    deps: set[str]
    explicit: set[str]
    remove: set[str]
    ignore: set[str]
    d2e: set[str]
    e2d: set[str]

    def __init__(
        self,
        deps: set[str] | None = None,
        explicit: set[str] | None = None,
        d2e: set[str] | None = None,
        e2d: set[str] | None = None,
        remove: set[str] | None = None,
        ignore: set[str] | None = None,
    ):
        self.deps = deps if deps else set()
        self.explicit = explicit if explicit else set()
        self.remove = remove if remove else set()
        self.ignore = ignore if ignore else set()
        self.d2e = d2e if d2e else set()
        self.e2d = e2d if e2d else set()


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
                    line = line.replace("\n", "").split("#")[0].strip()
                    if not line:
                        continue
                    options = line.split(" ")
                    if len(options) == 1:
                        apps.append(line)
                    elif (len(options) > 1) and (option := options[0]):
                        if "--asdeps" in line:
                            deps.append(option)

    return Expected(explicit=set(apps), deps=set(deps), ignore=set(ignore))


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
        e2d=(e2d := installed_explicit.intersection(expected.deps)),
        d2e=(d2e := installed_deps.intersection(expected.explicit)),
        remove=(
            installed_explicit
            - expected.explicit
            - installed_deps
            - expected.ignore
            - e2d
            - d2e
        ),
        explicit=(expected.explicit - installed_explicit - installed_deps),
        deps=(expected.deps - installed_deps - installed_explicit),
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
    if remove := needed.remove - needed.e2d - needed.d2e:
        query.append("yay -Rns " + " ".join(remove))
    if needed.deps:
        query.append("yay -S --asdeps " + " ".join(needed.deps))
    if needed.e2d:
        query.append("yay -D --asdeps " + " ".join(needed.e2d))
    if needed.explicit:
        query.append("yay -S " + " ".join(needed.explicit))
    if needed.d2e:
        query.append("yay -D --asexplicit " + " ".join(needed.d2e))
    if len(sys.argv) == 2:
        arg = sys.argv[1]
        if arg in ["-a", "--apply"]:
            subprocess.call(";".join(query), shell=True)
        elif arg in ["-h", "--help"]:
            sys.stdout.write(
                "Usage: run scripts without arguments to dry-run\n"
                + 'Use -a, --apply to apply result\nAdd packages you want to ignore in "./ignore"\n'
                + 'Add "_" as first char of file\'s name to disable group. For example: "de" >> "_de"'
            )
            sys.stdout.flush()
    else:
        sys.stdout.write(";".join(query))
        sys.stdout.flush()
