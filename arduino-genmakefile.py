#!/usr/bin/python3

# pylint: disable=invalid-name,missing-module-docstring,missing-class-docstring,missing-function-docstring

import argparse
import sys
import os
import glob
import subprocess
import re
import copy
import pathlib
import time
import enum
import yaml


class Constants:
    @staticmethod
    def generated_by_us_string():
        return "# Generated by arduino-genmakefile\n"

    @staticmethod
    def header_strings():
        cmd_line = sys.argv.copy()
        cmd_line[0] = os.path.basename(cmd_line[0])
        return [Constants.generated_by_us_string(),
                "#\n",
                "# Command line:\n",
                "# " + ' '.join(cmd_line) + "\n",
                "\n"]

    @staticmethod
    def default_debug_command():
        return "cat $$SERIALPORT"

    @staticmethod
    def default_baudrate():
        return "115200"


class Paths:
    @staticmethod
    def templates_dir():
        return Path(os.path.join(os.path.dirname(__file__), "templates"))

    @staticmethod
    def makefile_default_template_path():
        return Path(os.path.join(Paths.templates_dir().path, "Makefile"))

    @staticmethod
    def qmake_default_template_path():
        return Path(os.path.join(Paths.templates_dir().path, "qmake.pro"))


class Error:
    @staticmethod
    def exit_on_error(message):
        raise Exception(message)

    @staticmethod
    def exit_on_exception(message, exception):
        print(message)
        raise exception


class Path:
    # pylint: disable=too-many-public-methods
    class Type(enum.Enum):
        Relative = 0
        Absolute = 1
        User = 2

    @staticmethod
    def check_basedir_valid(basedir):
        basedir = Path.to_string(basedir)
        if basedir is None:
            raise ValueError("Base dir is None")
        if not os.path.isabs(basedir):
            raise ValueError("Base dir " + basedir + " is not valid (should be absolute)")
        if os.path.exists(basedir) and not os.path.isdir(basedir):
            raise ValueError("Base dir " + basedir + " is not valid (exists and is not a directory")
        return True

    @staticmethod
    def to_string(path):
        if isinstance(path, Path):
            return path.path
        return path

    def __init__(self, path, basedir=None):
        path = Path.to_string(path)
        basedir = Path.to_string(basedir)

        if path.startswith("~/"):
            # path is something like ~/some/path
            self._type = Path.Type.User
            self.basedir = os.path.expanduser("~/")
            self.path = os.path.realpath(os.path.expanduser(path))
        elif os.path.isabs(path):
            # path is something like /some/path
            self._type = Path.Type.Absolute
            self.path = os.path.realpath(path)
        else:
            # path is something like some/path, basedir something like /some/directory
            Path.check_basedir_valid(basedir)
            self._type = Path.Type.Relative
            self.basedir = basedir
            self.path = os.path.realpath(os.path.join(basedir, path))

    def __eq__(self, other):
        return self.path == other.path

    def to_relative(self, basedir):
        basedir = Path.to_string(basedir)
        Path.check_basedir_valid(basedir)
        return Path(os.path.relpath(self.path, basedir), basedir)

    def rel_path(self):
        if self._type == Path.Type.Absolute:
            raise ValueError("Calling rel_path() on an absolute path")
        return os.path.relpath(self.path, self.basedir)

    def with_extension(self, extension):
        ret = copy.deepcopy(self)
        ret.path = str(pathlib.Path(self.path).with_suffix(extension))
        return ret

    def isuser(self):
        return self._type == Path.Type.User

    def isabs(self):
        return self._type == Path.Type.Absolute

    def isrel(self):
        return self._type == Path.Type.Relative

    def exists(self):
        return os.path.exists(self.path)

    def isfile(self):
        return os.path.isfile(self.path)

    def isdir(self):
        return os.path.isdir(self.path)

    def isemptyfile(self):
        return self.isfile() and os.path.getsize(self.path) == 0

    def basename(self):
        return os.path.basename(self.path)

    def parent_dir(self):
        ret = copy.deepcopy(self)
        ret.path = os.path.dirname(self.path)
        return ret

    def generated_by_us(self):
        for line in self.read_lines():
            if line.startswith(Constants.generated_by_us_string()):
                return True
        return False

    def safely_remove_or_exit(self):
        if not self.exists():
            return
        if not self.isfile():
            Error.exit_on_error(self.path + " cannot be safely removed (not a file), please remove it manually")

        if not self.generated_by_us() and not self.isemptyfile():
            Error.exit_on_error(self.path + " cannot be safely removed (not empty, not generated by us), please remove it manually")

        os.remove(self.path)

    def read_lines(self):
        with open(self.path, "r", encoding="utf8") as file:
            lines = file.readlines()
        return lines

    def write_lines(self, lines):
        with open(self.path, "a", encoding="utf8") as file:
            file.writelines(lines)

    @staticmethod
    def list_from_key(key, config_dir):
        ret = []
        for path in key:
            ret.append(Path(path, config_dir))
        return ret

    @staticmethod
    def check_files_exist(paths):
        for path in paths:
            if not path.exists():
                raise FileNotFoundError(path.path + " doesn't exist")
            if not path.isfile():
                raise FileExistsError(path.path + " is not a file")

    @staticmethod
    def check_dirs_exist(paths):
        for path in paths:
            if not path.exists():
                raise FileNotFoundError(path.path + " doesn't exist")
            if not path.isdir():
                raise FileExistsError(path.path + " is not a directory")


class Config:
    # pylint: disable=too-many-instance-attributes
    extra_config_stack = []

    def __init__(self, paths):
        # pylint: disable=too-many-branches
        self.main_paths = paths.copy()
        self.paths = []
        for path in paths:
            self.paths.append(path)
            self.paths += Config.get_extra_configs(path)

        self.fqbn = None
        self.cflags = []
        self.debug_command = "cat $$SERIALPORT"
        self.baudrate = "115200"
        self.lib_paths = []
        self.qmake_dirs = []
        self.qmake_exclude_dirs = []

        for path in self.paths:
            try:
                with open(path.path, "r", encoding="utf8") as file:
                    data = yaml.safe_load(file)
            except OSError as exception:
                Error.exit_on_exception("Failed opening configuration file", exception)
            except yaml.YAMLError as exception:
                Error.exit_on_exception("Failed parsing configuration file", exception)

            for key in data.keys():
                if key == "fqbn":
                    self.fqbn = data[key]
                elif key == "cflags":
                    self.cflags += data[key]
                elif key == "debug_command":
                    self.debug_command = data[key]
                elif key == "baudrate":
                    self.baudrate = data[key]
                elif key == "libs":
                    self.lib_paths += Path.list_from_key(data[key], path.parent_dir())
                elif key == "qmake_dirs":
                    self.qmake_dirs += Path.list_from_key(data[key], path.parent_dir())
                elif key == "qmake_exclude_dirs":
                    self.qmake_exclude_dirs += Path.list_from_key(data[key], path.parent_dir())
                elif key == "configs":
                    # Already handled
                    pass
                else:
                    print("Warning: unhandled key " + key + " in configuration file " + str(path))

        if self.fqbn is None:
            Error.exit_on_error("Missing fqbn field in configuration")

        print()
        print("Loaded configuration:")
        print(str(self))
        print()

    @staticmethod
    def title_string(title):
        return " * " + title + ":"

    @staticmethod
    def item_string(item):
        return "   - " + item

    def __str__(self):
        ret = []

        ret.append(Config.title_string("main configuration paths"))
        for path in self.main_paths:
            ret.append(Config.item_string(path.path))

        ret.append(Config.title_string("sub configurations"))
        for path in self.paths:
            if path not in self.main_paths:
                ret.append(Config.item_string(path.path))

        ret.append(Config.title_string("fqbn"))
        ret.append(Config.item_string(self.fqbn))

        ret.append(Config.title_string("libs"))
        for lib_path in self.lib_paths:
            ret.append(Config.item_string(lib_path.path))

        ret.append(Config.title_string("cflags"))
        for cflag in self.cflags:
            ret.append(Config.item_string(cflag))

        return '\n'.join(ret)

    @staticmethod
    def get_extra_configs(path):
        if path in Config.extra_config_stack:
            print("Circular configuration inclusion detected while parsing " + path.path)
            print("Inclusion stack: ")
            for stack_item in Config.extra_config_stack:
                print(" - " + stack_item.path)
            Error.exit_on_error("Aborting due to circular configuration inclusion")

        Config.extra_config_stack.append(path)
        ret = []
        with open(path.path, "r", encoding="utf8") as file:
            data = yaml.safe_load(file)

        for config in data.get("configs", []):
            config_path = Path(config, path.parent_dir())
            ret.append(config_path)
            ret += Config.get_extra_configs(config_path)

        Config.extra_config_stack.pop()
        return ret


class Makefile:
    def __init__(self, config, path, template_path, sketch_path):
        self.path = path
        self.config = config
        self.sketch_path = sketch_path.to_relative(path.parent_dir())
        self.template_path = template_path

    def generate(self):
        self.path.safely_remove_or_exit()

        print("Generating " + self.path.path + "...")
        in_lines = self.template_path.read_lines()
        out_lines = Constants.header_strings()
        for line in in_lines:
            out_lines += self.replace_tokens(line, self.sketch_path)
        self.path.write_lines(out_lines)
        print("Done")

    def replace_tokens(self, line, sketch_path):
        # pylint: disable=too-many-return-statements,too-many-branches
        if "LIBS_PLACEHOLDER" in line:
            ret = []
            Path.check_dirs_exist(self.config.lib_paths)
            for lib_path in self.config.lib_paths:
                if lib_path.isuser():
                    lib_path_string = os.path.join("$(HOME)", lib_path.rel_path())
                elif lib_path.isrel():
                    lib_path_string = os.path.join("$(MAKEFILE_DIR)", lib_path.to_relative(self.path.parent_dir()).rel_path())
                else:
                    lib_path_string = str(lib_path)
                ret.append("\t\t--library \"" + lib_path_string + "\" \\\n")
            return ret
        if "FQBN_PLACEHOLDER" in line:
            return [line.replace("FQBN_PLACEHOLDER", self.config.fqbn)]
        if "BINDIR_PLACEHOLDER" in line:
            bindir = "bin"
            bindir_suffix = self.path.basename().replace("Makefile", "", 1)
            if bindir_suffix:
                bindir += bindir_suffix
            return [line.replace("BINDIR_PLACEHOLDER", bindir)]
        if "BINFILE_PLACEHOLDER" in line:
            return [line.replace("BINFILE_PLACEHOLDER", os.path.basename(sketch_path.with_extension(".ino.bin").path))]
        if "CFLAGS_PLACEHOLDER" in line:
            return [line.replace("CFLAGS_PLACEHOLDER", ' '.join(self.config.cflags))]
        if "SKETCH_NOEXT_PLACEHOLDER" in line:
            return [line.replace("SKETCH_NOEXT_PLACEHOLDER", sketch_path.to_relative(self.path.parent_dir()).
                                 with_extension("").rel_path())]
        if "DEBUG_COMMAND_PLACEHOLDER" in line:
            return [line.replace("DEBUG_COMMAND_PLACEHOLDER", self.config.debug_command)]
        if "BAUDRATE_PLACEHOLDER" in line:
            return [line.replace("BAUDRATE_PLACEHOLDER", self.config.baudrate)]

        return [line]


class Qmake:
    # pylint: disable=too-many-instance-attributes
    def __init__(self, config, path, template_path, sketch_path, makefile_path):
        # pylint: disable=too-many-arguments
        self.path = path
        self.prifile_path = self.path.with_extension(".pri")
        self.config = config
        self.template_path = template_path
        self.prifile_template_path = template_path.with_extension(".pri")
        self.sketch_path = sketch_path.to_relative(self.path.parent_dir())
        self.makefile_path = makefile_path
        self.included_dirs = [self.sketch_path.parent_dir()] + config.lib_paths + config.qmake_dirs
        self.excluded_dirs = config.qmake_exclude_dirs
        self.script_path = self.path.with_extension("")

    @staticmethod
    def headers_dirs(headers):
        ret = []
        # Store the previous header dir to avoid calling 'if header_dir not in ret' for each header file
        prev_header_dir = None
        for header in headers:
            if prev_header_dir and prev_header_dir == header.parent_dir():
                continue
            header_dir = header.parent_dir()
            prev_header_dir = header_dir
            if header_dir not in ret:
                ret.append(header_dir)

        return ret

    def generate(self):
        self.path.safely_remove_or_exit()
        self.prifile_path.safely_remove_or_exit()

        print("Scanning files for qmake generation...")
        print("Getting \"OTHER_FILES\"...")
        other_files = self.get_other_files()
        print("Getting \"HEADERS\"...")
        headers = self.get_files([".h", ".hpp"])
        print("Getting \"SOURCES\"...")
        sources = self.get_files([".c", ".cpp"])
        sources.insert(0, self.sketch_path)
        print("Getting \"INCLUDEPATH\"...")
        includepaths = Qmake.headers_dirs(headers)
        print("Done")

        defines = Qmake.get_defines(self.makefile_path)

        print("Generating " + self.path.path + "...")
        in_lines = self.template_path.read_lines()
        out_lines = Constants.header_strings()
        for line in in_lines:
            out_lines += self.replace_tokens(line, other_files, headers, sources, includepaths, defines,
                                             include_abs=False, include_rel=True, include_user=False)
        self.path.write_lines(out_lines)
        print("Done")

        print("Generating " + self.prifile_path.path + "...")
        in_lines = self.prifile_template_path.read_lines()
        out_lines = Constants.header_strings()
        for line in in_lines:
            out_lines += self.replace_tokens(line, other_files, headers, sources, includepaths, defines,
                                             include_abs=True, include_rel=False, include_user=True)
        self.prifile_path.write_lines(out_lines)
        print("Done")

        self.create_runscript()

    # Generate a script that will be called by qtcreator when we run the project
    def create_runscript(self):
        self.script_path.safely_remove_or_exit()

        makefile_rel_path = self.makefile_path.to_relative(self.script_path.parent_dir())
        out_lines = ["#!/bin/sh\n"] + Constants.header_strings() + ["make -f " + makefile_rel_path.rel_path() + " run\n"]
        self.script_path.write_lines(out_lines)
        os.chmod(self.script_path.path, 0o0755)

    def replace_tokens(self, line, other_files, headers, sources, includepaths, defines, include_abs, include_rel, include_user):
        # pylint: disable=too-many-arguments,too-many-locals
        qmake_dir = self.path.parent_dir()
        if "TARGET_PLACEHOLDER" in line:
            return [line.replace("TARGET_PLACEHOLDER", self.script_path.with_extension("").to_relative(qmake_dir).rel_path())]
        if "MAKEFILE_PLACEHOLDER" in line:
            return [line.replace("MAKEFILE_PLACEHOLDER", self.makefile_path.to_relative(qmake_dir).rel_path())]
        if "PRIFILE_PLACEHOLDER" in line:
            return [line.replace("PRIFILE_PLACEHOLDER", self.prifile_path.to_relative(qmake_dir).rel_path())]
        if "DEFINES_PLACEHOLDER" in line:
            ret = []
            for define in defines:
                ret.append("\t" + Qmake.to_qmake_define(define) + " \\\n")
            return ret

        paths = None

        if "OTHER_FILES_PLACEHOLDER" in line:
            paths = other_files
        elif "SOURCES_PLACEHOLDER" in line:
            paths = sources
        elif "HEADERS_PLACEHOLDER" in line:
            paths = headers
        elif "INCLUDEPATH_PLACEHOLDER" in line:
            paths = includepaths

        if paths is not None:
            ret = []
            for path in paths:
                # Don't consider user paths as relative, or we'll have them in the pro and pri files
                isrel = path.isrel() and not path.isuser()
                # pylint: disable=too-many-boolean-expressions
                if isrel and include_rel or path.isuser() and include_user or path.isabs() and include_abs:
                    ret.append(Qmake.to_qmake_file_directive(path, self.path))
            return ret

        # Nothing to replace
        return line

    @staticmethod
    def is_rawpath_excluded(raw_real_path, excluded_dirs):
        for excluded_dir in excluded_dirs:
            if raw_real_path.startswith(str(excluded_dir)):
                return True
        return False

    def get_other_files(self):
        return [self.makefile_path] + self.config.paths

    @staticmethod
    def raw_path_in_paths(raw_path, paths):
        for path in paths:
            if str(path) == os.path.realpath(raw_path):
                return True
        return False

    def get_files(self, extensions):
        ret = []
        raw_paths = []
        for included_dir in self.included_dirs:
            for raw_path in glob.iglob(os.path.join(included_dir.path, "**"), recursive=True):
                raw_real_path = os.path.realpath(raw_path)
                if Qmake.is_rawpath_excluded(raw_real_path, self.excluded_dirs):
                    continue
                if not os.path.isfile(raw_real_path):
                    continue
                if os.path.splitext(raw_real_path)[-1] not in extensions:
                    continue
                if raw_real_path in raw_paths:
                    continue
                ret.append(Qmake.path_from_ancestor(included_dir, self.path, raw_real_path))
                raw_paths.append(os.path.realpath(raw_real_path))
        return ret

    @staticmethod
    def path_from_ancestor(ancestor, qmake_path, raw_path):
        if ancestor.isuser():
            new_path = Path(os.path.join("~/", os.path.relpath(raw_path, os.path.expanduser("~/"))))
        elif ancestor.isabs():
            new_path = Path(raw_path)
        else:
            new_path = Path(raw_path).to_relative(qmake_path.parent_dir())
        return new_path

    @staticmethod
    def to_qmake_file_directive(file_path, qmake_path):
        if file_path.isuser():
            path_string = "$$HOME/" + file_path.rel_path()
        elif file_path.isabs():
            path_string = file_path.path
        else:
            path_string = file_path.to_relative(qmake_path.parent_dir()).rel_path()
        return "\t" + path_string + " \\\n"

    @staticmethod
    def to_qmake_define(define):
        # Remove leading '-D'
        define = define[2:]
        define = define.replace("\\\"", "\\\\\\\"")
        return define

    @staticmethod
    def make_rule(makefile_path, rule):
        build_cmd = ["make", "-C", os.path.dirname(makefile_path.path), "-f", makefile_path.path, rule]
        return subprocess.check_output(build_cmd, stderr=subprocess.PIPE).decode("utf8")

    @staticmethod
    def get_defines(makefile_path):
        defines = []
        print("Building sketch to check proprocessor defines...")
        try:
            Qmake.make_rule(makefile_path, "clean")
            output = Qmake.make_rule(makefile_path, "build")
            Qmake.make_rule(makefile_path, "clean")
            print("Done")
        except subprocess.CalledProcessError as e:
            print("Got an exception while building the project, DEFINES variable won't be set in your qmake project")
            print("Build output was:")
            print()
            print("***")
            print(e.stderr.decode("utf8"))
            print("***")
            print()
            return []

        # Convert the raw output to an array of command lines issued during compilation
        cmd = ""
        cmds = []
        for line in output.splitlines():
            cmd += line
            if cmd.endswith("\\"):
                cmd = cmd[:-1]
                continue
            if cmd:
                cmds.append(cmd)
            cmd = ""

        for cmd in cmds:
            # Skip the line which contains arduino-cli, we'll check only the compiler output
            if cmd.split()[0].endswith("arduino-cli"):
                continue
            # This is a pretty dirty trick to handle the \" in the compiler command line
            # There is probably a much better way to handle them, but this seems to work decently...
            cmd = cmd.replace("\\\"", "BACKSLASH_QUOTE")
            quoted_strings = re.findall(r'"([^"]*)"', cmd)
            for quoted_string in quoted_strings:
                if quoted_string.startswith("-D"):
                    define = quoted_string.replace("BACKSLASH_QUOTE", "\\\"")
                    if define not in defines:
                        defines.append(define)

            tokens = cmd.split()
            for token in tokens:
                if (token.startswith("-D") or token.startswith("\"-D") or token.startswith("\'-D")) \
                        and "BACKSLASH_QUOTE" not in token:
                    if token not in defines:
                        defines.append(token)

        return defines


def main():
    description = """
Generate a Makefile and optionally a qmake project for an Arduino project.
This allows building the arduino project from command line,
and edit, build and run the project from QtCreator.
In both cases, you need to have arduino-cli installed and included in your PATH.
The generation is based on some yaml configuration files.
Please refer to the file README.md for more information.
"""
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--sketch", help="Arduino sketch path", required=True)
    parser.add_argument("--config", help="Configuration file path, may be passed multiple times", action='append', required=True)
    parser.add_argument("--makefile", help="Makefile generation path", required=True)
    parser.add_argument("--makefile-template", help="Makefile template path", required=False)
    parser.add_argument("--qmake", help="qmake project generation path. If not passed, no qmake project is generated", required=False)
    parser.add_argument("--qmake-template", help="qmake project template path", required=False)

    args = parser.parse_args()

    sketch_path = Path(args.sketch, os.getcwd())

    config_paths = []
    for config in args.config:
        config_paths.append(Path(config, os.getcwd()))

    required_files = [sketch_path] + config_paths

    if not os.path.basename(args.makefile).startswith("Makefile"):
        Error.exit_on_error("Please use a Makefile base name starting with \"Makefile\"")

    makefile_path = Path(args.makefile, os.getcwd())
    makefile_template_path = Path(args.makefile_template, os.getcwd()) if args.makefile_template else Paths.makefile_default_template_path()
    required_files.append(makefile_template_path)

    qmake_path = Path(args.qmake, os.getcwd()) if args.qmake else None
    if qmake_path:
        if not args.qmake.endswith(".pro"):
            Error.exit_on_error("Please use a qmake file name ending with \".pro\"")
        qmake_template_path = Path(args.qmake_template, os.getcwd()) if args.qmake_template else Paths.qmake_default_template_path()
        required_files.append(qmake_template_path)

    Path.check_files_exist(required_files)

    config = Config(config_paths)

    start_time = time.monotonic_ns()

    makefile = Makefile(config, makefile_path, makefile_template_path, sketch_path)
    makefile.generate()

    if qmake_path:
        qmakefile = Qmake(config, qmake_path, qmake_template_path, sketch_path, makefile_path)
        qmakefile.generate()

    end_time = time.monotonic_ns()

    print("Files generated in " + format((end_time - start_time) / 1000000000, ".3f") + " seconds")


if __name__ == '__main__':
    main()
