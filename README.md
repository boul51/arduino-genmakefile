# Description
The goal of this script is to generate a Makefile and optionally a QtCreator qmake project for an Arduino sketch.<br>
It generates a Makefile which relies on ```arduino-cli```, and allows building and running an Arduino project from command line.<br>
It can also generate a qmake project, from which you can edit, build and run the Arduino project.<br>
This can be useful if you prefer working from command line or want to use a non Arduino IDE (e.g. QtCreator)<br>
Several options can be set using some yaml configuration files.

# Prerequisites
## OS
The script works only under Linux. Since it relies on ```python3```, it should be quite easy to port to a different platform.

## arduino-cli
The script expects ```arduino-cli``` to belong to your ```PATH``` variable.

## python3
The script relies on ```python3``` and the ```pyyaml``` python package.

# How to use it
## Create some configuration files
Create one or several yaml configuration files (check the "variables" paragraph from more information)<br>
A minimal configuration consists of the ```fqbn``` variable. 

## Invoke the generation script
Launch the script to generate your project files.<br>
Example:<br>
```arduino-genmakefile.py --sketch mysketch.ino --config myconf.yaml --makefile Makefile.myconf --qmake mysketch_myconf.pro```  

## Invoke make
The script generates a Makefile with three targets:

### build
Compile the sketch:<br>
```make -f <Makefile-path>```

### run
Compile and upload the sketch, and run the specified debug command (cf ```debug_command``` variable):<br>
```make -f <Makefile-path> run```

### clean
Clean the build:<br>
```make -f <Makefile-path> clean```

## Open project from qtcreator

If you passed the ```--qmake <path>``` option, you can build and run the Arduino project from QtCreator:
 - open the generated ```.pro``` file from QtCreator
 - select any Qt configuration (it doesn't matter since we'll build using arduino-cli)
 - uncheck the ```Build Settings/General/Shadow build``` option
 - remove the ```Build Settings/Build steps/qmake``` step
 - uncheck the ```Run settings/Run/Run in terminal``` option
   (except if you want to run your debug command in a terminal, e.g. when you using minicom as debug command)

You can now use the QtCreator build and run commands.

**Note:** Along with the ```.pro``` file, a ```.pri``` file with the same prefix is created (cf below).

**Note:** In order to have better auto-completion and syntax highlighting in QtCreator,
the script attempts to set the ```HEADERS```, ```SOURCES``` and ```INCLUDEPATH``` qmake variables.
For this, it scans your ```libs``` variable directories.<br> 
Additionally, some paths can be added or removed using the ```qmake_dirs``` and ```qmake_excluded_dirs``` variables.<br>
The script also attemps to set the ```DEFINES``` variable to the qmake file by checking the compiler output.<br>

The ```HEADERS```, ```SOURCES```, ```INCLUDEPATH``` and ```DEFINES``` variables have **no impact** on the compilation.<br>
They are used **only** for syntax highlighting and source code navigation in QtCreator.

The script will try to keep as many relative paths as possible, so that the ```.pro``` and ```.pri``` files can be added to SCM.<br>
Additionnally, when the paths start with ```~/```, the ```~/``` will be expanded to ```$$HOME``` in the qmake files.<br>
Relative paths are added to the ```.pro``` file, while absolute paths are added to the ```.pri``` file.<br>
This can be practical if you wish to add only the ```.pro``` file to SCM.<br> 

# Variables
Several variables can be set in your yaml configuration files.<br>
It is possible to include several configuration files by passing several times the ```--config``` option.<br>
It is also possible to "include" some additional configuration files from a configuration file. (cf ```configs``` variable)   

## fqbn
 - type: string
 - default: **none**
 - description: the "fully qualified board name". All valid fqbns can be obtained with command ```arduino-cli board listall```
 - example value:
```
fqbn: arduino:sam:arduino_due_x
```

Note: this is the only **mandatory** variable. 

## configs
 - type: array of strings
 - default: ```[]```
 - description: some additional configuration files to be used 
 - example value:
```
configs:
    - ~/conf/common-config.yaml
    - conf/project-config.yaml
```
Notes:
 - when a path is relative, the directory of the configuration file where it is declared is prepended
 - if an array variable is present in several files, the values are merged
 - if a scalar variable is present in several files, the last found value is used 

## cflags
 - type: array of strings
 - default: ```[]```
 - description: additional flags passed to the preprocessor and compiler. It uses the ```--build-property
   compiler.cpp.extra_flags``` option of ```arduino-cli``` 
 - example value:
```
cflags:
    - -Wall
    - -I"$(CURDIR)"
    - -DNO_PRAGMA_MARK
    - -DSERIAL_IFACE=SerialUSB
    - '"-DMY_STRING="SOME STRING""'
```

## libs
 - type: array of strings
 - default: ```[]```
 - description: additional libraries paths. It uses the ```--library``` option of ```arduino-cli```
 - example value:
```
libs:
 - libs/lib1
 - ~/libs/mycommonlib
```
**Note:** when a path is relative, the directory of the configuration file where it is declared is prepended

## debug_command
 - type: string
 - default: ```cat $$SERIALPORT```
 - description: command to be run by the ```make run``` rule 
 - example value:
```
debug_command: minicom -D $$SERIALPORT
```
**Note:** The ```SERIALPORT``` variable is set internally by the Makefile run target, it will be set to the serial device
matching the attached board with the given fqbn (e.g. ```/dev/ttyACM0```) 
## baudrate
 - type: string
 - default: ```115200```
 - description: the baudrate to be set before starting the debug command
 - example value:
```
baudrate: 9600
```
## qmake_dirs
 - type: string array
 - default: ```[]```
 - description: the list of additional paths to be scanned to add sources to the qmake project
 - example value:
```
qmake_dirs:
 - "~/.arduino15/packages/arduino/hardware/sam"
 - "~/.arduino15/packages/arduino/tools/arm-none-eabi-gcc"
```
**Note:** you'll probably want to use different values here depending on your board.
**Note:** when a path is relative, the directory of the configuration file where it is declared is prepended

## qmake_exclude_dirs
  - type: string array
  - default: ```[]```
  - description: the list of paths to be excluded from ```qmake_dirs```.
    This can be useful if you add a directory with a lot of sources, but want to exclude part of it.
  - example value:
```
qmake_exclude_dirs:
 - "~/.arduino15/packages/arduino/hardware/avr"
```
**Note:** when a path is relative, the directory of the configuration file where it is declared is prepended

# Templates
The script is uses templates for the Makefile and qmake project, located in the ```templates``` directory.<br>
You can select some different templates using the ```--makefile-template``` and ```--qmake-template``` options.

# Sample project
You can refer to the ```tests/simple``` directory, which contains a sample project.
