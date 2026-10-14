.PHONY: build clean serve test check

build:
	PYTHONPATH=src python -m florica_site.build

clean:
	rm -rf dist

serve: build
	python -m http.server 8000 --directory dist

test:
	PYTHONPATH=src python -m unittest discover -s tests -v

check: test build
