.PHONY: bin deps

all: bin deps

deps:
	@git submodule update --init

bin:
	@rm -f ../../bin/retro-display
	@cd ../../bin && ln -s ../plugins/display/scripts/retro-display.py retro-display
	@rm -f ../../lib/python/display.py
	@cd ../../lib/python && ln -s ../../plugins/display/lib/python/display.py display.py
