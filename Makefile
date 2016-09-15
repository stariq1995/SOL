.PHONY: all
all:
	python setup.py build_ext --inplace

.PHONY: clean
clean:
	rm -r build
	find . -name '*.c' -exec rm {} \;
	find . -name '*.so' -exec rm {} \;

.PHONY: watch
watch:
	bash watch.sh
