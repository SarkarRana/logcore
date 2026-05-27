# Minimal Makefile for local Sphinx builds.
# Usage:
#   make html       — build the HTML site under _build/html
#   make clean      — remove the build directory
#   make serve      — serve the built site on http://localhost:8000

SPHINXBUILD ?= sphinx-build
SOURCEDIR   = .
BUILDDIR    = _build

.PHONY: html clean serve

html:
	$(SPHINXBUILD) -b html -W --keep-going $(SOURCEDIR) $(BUILDDIR)/html

clean:
	rm -rf $(BUILDDIR)

serve: html
	@echo "Serving on http://localhost:8000 — Ctrl+C to stop"
	@cd $(BUILDDIR)/html && python -m http.server 8000
