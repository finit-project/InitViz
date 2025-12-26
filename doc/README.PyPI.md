# Building and Publishing to PyPI

This document describes how to build and publish InitViz to PyPI.

## Prerequisites

Install build tools:

```bash
pip install build twine
```

Or use the dev extras:

```bash
pip install -e ".[dev]"
```

## System Dependencies

InitViz requires GTK3 and Cairo, which must be installed via your system
package manager.

**Debian/Ubuntu:**

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

**Fedora:**

```bash
sudo dnf install python3-gobject python3-cairo gtk3
```

## Building

1. Ensure `initviz/main.py` is generated from `main.py.in`:

   ```bash
   make python
   ```

2. Build the distribution packages:

   ```bash
   python -m build
   ```

This creates both `.tar.gz` (source) and `.whl` (wheel) packages in `dist/`.

## Local Testing

Install locally in development mode:

```bash
pip install -e .
```

Or test the built package:

```bash
pip install dist/initviz-0.14.9-py3-none-any.whl
```

## Publishing

### Test on TestPyPI first

1. Upload to TestPyPI:

   ```bash
   python -m twine upload --repository testpypi dist/*
   ```

2. Test installation from TestPyPI:

   ```bash
   pip install --index-url https://test.pypi.org/simple/ initviz
   ```

### Publish to PyPI

Once tested, upload to the real PyPI:

```bash
python -m twine upload dist/*
```

## Version Management

The version is managed in two places:

- `pyproject.toml` - Single source of truth for PyPI
- `initviz/__init__.py` - Exports `__version__` and `get_version()`
- `Makefile` - VER variable (for traditional builds)

When releasing, update all three locations.

## Notes

- The PyPI package installs only the Python visualization tool (`initviz`)
- The C collector (`bootchartd`) must be installed separately or via system packages
- GTK3/Cairo dependencies are listed in `pyproject.toml` but users must
  install them via system packages
