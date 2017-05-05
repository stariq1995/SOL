.PHONY: all
all:
	python setup.py build_ext --inplace

.PHONY: clean
clean:
	rm -rf ./build
	find . -name '*.c' -exec rm {} \;
	find . -name '*.so' -exec rm {} \;
	find . \( -name '__pycache__' -type d \) -prune -exec rm -rf {} \;

.PHONY: watch
watch:
	bash watch.sh
