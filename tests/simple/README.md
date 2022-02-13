# About this folder
This folder contains a simple test sketch, and several configuration files.
It links against two small libraries, lib1 and lib2.

# Examples:

## Generate and run project for arduino due using native USB port
```
../../arduino-genmakefile.py --sketch simple.ino --makefile Makefile.due_native --qmake simple_due_native.pro --config simple_due_native.yaml
make -f Makefile.due_native run
```

## Generate and run project for arduino due using programming USB port
```
../../arduino-genmakefile.py --sketch simple.ino --makefile Makefile.due_prog --qmake simple_due_prog.pro --config simple_due_prog.yaml
make -f Makefile.due_prog run
```

## Generate and run project for nanoevery
```
../../arduino-genmakefile.py --sketch simple.ino --makefile Makefile.nanoevery --qmake simple_nanoevery.pro --config simple_nanoevery.yaml
make -f Makefile.nanoevery run
```

## Generate and run project for nanoevery, using minicom -D as debug command
```
../../arduino-genmakefile.py --sketch simple.ino --makefile Makefile.nanoevery --qmake simple_nanoevery.pro --config simple_nanoevery.yaml --config conf/debug/minicom.yaml
make -f Makefile.nanoevery run
```
