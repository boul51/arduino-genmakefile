export MAKEFILE_PATH = $(abspath $(lastword $(MAKEFILE_LIST)))
export MAKEFILE_DIR = $(dir $(MAKEFILE_PATH))
export BINDIR="$(MAKEFILE_DIR)/BINDIR_PLACEHOLDER"
export BINFILE="$(BINDIR)/BINFILE_PLACEHOLDER"

export FQBN = "FQBN_PLACEHOLDER"

all: build

build:
	arduino-cli compile "$(MAKEFILE_DIR)/SKETCH_NOEXT_PLACEHOLDER" \
		--verbose \
		--fqbn $(FQBN) \
		--warnings all \
		--build-property 'compiler.cpp.extra_flags=CFLAGS_PLACEHOLDER' \
		--build-property 'compiler.c.extra_flags=CFLAGS_PLACEHOLDER' \
		LIBS_PLACEHOLDER \
		--output-dir $(BINDIR)

run: build
	@echo "Searching board type $(FQBN)"; \
	SERIALPORT=`arduino-cli board list | grep "$(FQBN)" | awk '{print $$1}'`; \
	if [ -z $$SERIALPORT ]; then \
		echo "No serial port found"; \
		exit 1; \
	fi; \
	echo "Found board $(FQBN) on port $$SERIALPORT"; \
	echo "Killing apps holding serial port"; \
	for pid in `lsof -t $$SERIALPORT`; do \
		echo killing PID "$$pid"; \
		kill -9 $$pid; \
	done; \
	echo "Starting upload"; \
	arduino-cli upload --fqbn $(FQBN) --port $$SERIALPORT --input-file $(BINFILE); \
	sleep 1; \
	echo "Waiting for serial port to settle"; \
	while [ ! -e $$SERIALPORT ]; do sleep 0.1; done; \
	echo "Serial port is ready"; \
	stty raw -F $$SERIALPORT -echo BAUDRATE_PLACEHOLDER; \
	echo "Starting command: DEBUG_COMMAND_PLACEHOLDER"; \
	DEBUG_COMMAND_PLACEHOLDER;

clean:
	rm -rf /tmp/arduino-sketch-*
	rm -rf $(BINDIR)
