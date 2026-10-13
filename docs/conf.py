"""Sphinx configuration for heatmiserv3 documentation."""
import os
import sys

# Ensure heatmiserv3 package is on sys.path for autodoc
sys.path.insert(0, os.path.abspath(".."))

project = "heatmiserv3"
copyright = "2026, Andy Loughran"
author = "Andy Loughran"
release = "3.0.0"

extensions = [
    "myst_parser",
    "sphinx_rtd_theme",
    "sphinx_copybutton",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

root_doc = "index"

# Exclude GitHub Pages static files, build output, and redundant ADR README
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "index.html",
    "twin.html",
    "adrs/README.md",
]

# MyST Markdown Parser options
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "tasklist",
]
myst_heading_anchors = 4

# HTML output options
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "collapse_navigation": False,
    "sticky_navigation": True,
    "navigation_depth": 4,
}

# Autodoc settings
autodoc_member_order = "bysource"
autodoc_typehints = "description"
