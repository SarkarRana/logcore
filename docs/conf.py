"""Sphinx configuration for the LogCore documentation site."""

from __future__ import annotations

import os
import sys
from datetime import datetime

# Make the logcore package importable for autodoc.
sys.path.insert(0, os.path.abspath(".."))

import logcore  # noqa: E402

# -- Project information --------------------------------------------------

project = "LogCore"
author = "LogCore Contributors"
copyright = f"{datetime.now().year}, {author}"
release = logcore.__version__
version = ".".join(release.split(".")[:2])

# -- General configuration ------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    "myst_parser",
]

autosummary_generate = False  # we hand-curate the entries in api.md

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

master_doc = "index"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- MyST (Markdown) ------------------------------------------------------

myst_enable_extensions = [
    "colon_fence",      # ::: directives
    "deflist",
    "fieldlist",
    "tasklist",
]
myst_heading_anchors = 3  # auto-generate anchors for h1-h3

# -- Autodoc --------------------------------------------------------------

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
    "member-order": "bysource",
}
autodoc_typehints = "description"   # render types in the description, not signatures
autodoc_typehints_format = "short"  # strip module prefixes (`Optional` not `typing.Optional`)
always_document_param_types = True
typehints_use_signature_return = True

# Don't pull in private members (anything prefixed with _).
def _skip_private(app, what, name, obj, skip, options):
    if name.startswith("_") and not name.startswith("__"):
        return True
    return skip


def setup(app):
    app.connect("autodoc-skip-member", _skip_private)


# -- Intersphinx ----------------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# -- HTML output ----------------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_static_path: list[str] = []  # add "_static" once you have custom CSS/JS
html_title = f"LogCore {release}"
html_show_sourcelink = False
html_theme_options = {
    "collapse_navigation": False,
    "navigation_depth": 3,
    "prev_next_buttons_location": "both",
    "style_external_links": True,
}
