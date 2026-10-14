.PHONY: build clean evidence serve test check

build:
	PYTHONPATH=src python -m florica_site.build

clean:
	rm -rf dist release .preview

serve: build
	rm -rf .preview
	mkdir -p .preview
	cp -R dist .preview/floricaltd-static-website
	python -m http.server 8000 --directory .preview

evidence: build
	python scripts/create_release_evidence.py --source-sha "$$(git rev-parse HEAD)"

test:
	PYTHONPATH=src python -m unittest discover -s tests -v

check: test build
