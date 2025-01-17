# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright 2016-2024 Stéphane Caron and the qpsolvers contributors

import re
import sys
from os.path import abspath, dirname, join

sys.path.insert(0, abspath(".."))

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx-mathjax-offline",
    "sphinx.ext.napoleon",  # before sphinx_autodoc_typehints
    "sphinx_autodoc_typehints",
]

# List of modules to be mocked up
autodoc_mock_imports = [
    "ecos",
    "gurobipy",
    "hpipm_python",
    "mosek",
    "nppro",
    "osqp",
    "qpoases",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = []

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "qpsolvers"
copyright = "2016-2024 Stéphane Caron and the qpsolvers contributors"
author = "Stéphane Caron"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.

# The short X.Y version.
version = None

# The full version, including alpha/beta/rc tags.
release = None

# Read version info directly from the module's __init__.py
init_path = join(dirname(dirname(str(abspath(__file__)))), "qpsolvers")
with open(f"{init_path}/__init__.py", "r") as fh:
    for line in fh:
        match = re.match('__version__ = "((\\d.\\d).\\d)[a-z0-9\\-]*".*', line)
        if match is not None:
            release = match.group(1)
            version = match.group(2)
            break

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ["build", "Thumbs.db", ".DS_Store"]

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "furo"

# Override Pygments style.
pygments_style = "sphinx"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = {}

# Output file base name for HTML help builder.
htmlhelp_basename = "qpsolversdoc"
