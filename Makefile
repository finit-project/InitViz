VER            = 0.14.9
PKG_NAME       = initviz
PKG_TARBALL    = $(PKG_NAME)-$(VER).tar.gz

CROSS_COMPILE ?= $(CONFIG_CROSS_COMPILE:"%"=%)
CC            ?= $(CROSS_COMPILE)gcc
CFLAGS        ?= -g -Wall -O0
CPPFLAGS      ?=

# Normally empty, but you can use program_prefix=mmeeks- or program_suffix=2
# to install bootchart2 on a system that already has other projects that also
# call themselves bootchart.
PROGRAM_PREFIX ?=
PROGRAM_SUFFIX ?=

# Prefix for things that must reside on the root filesystem.
# "" for e.g. Debian; /usr for distributions with /usr unification.
EARLY_PREFIX   ?=

BINDIR         ?= /usr/bin
PYTHON         ?= python3
DOCDIR         ?= /usr/share/doc/initviz
MANDIR         ?= /usr/share/man/man1
# never contains /usr; typically /lib, /lib64 or e.g. /lib/x86_64-linux-gnu
LIBDIR         ?= /lib
PKGLIBDIR      ?= $(EARLY_PREFIX)$(LIBDIR)/$(PROGRAM_PREFIX)bootchart$(PROGRAM_SUFFIX)

ifndef PY_LIBDIR
ifndef NO_PYTHON_COMPILE
PY_LIBDIR      := $(shell $(PYTHON) -c "from distutils import sysconfig; print(sysconfig.get_config_var('DESTLIB'))")
else
PY_LIBDIR       = /usr$(LIBDIR)/python2.6
endif
endif
PY_SITEDIR     ?= $(PY_LIBDIR)/site-packages
LIBC_A_PATH     = /usr$(LIBDIR)
COLLECTOR       = \
	collector/collector.o \
	collector/output.o \
	collector/tasks.o \
	collector/tasks-netlink.o \
	collector/dump.o

collector: \
	bootchart-collector \
	bootchartd

python: \
	VERSION \
	initviz/main.py

all: collector python

%.o:%.c
	$(CC) $(CFLAGS) $(LDFLAGS) -pthread \
		-DEARLY_PREFIX='"$(EARLY_PREFIX)"' \
		-DLIBDIR='"$(LIBDIR)"' \
		-DPKGLIBDIR='"$(PKGLIBDIR)"' \
		-DPROGRAM_PREFIX='"$(PROGRAM_PREFIX)"' \
		-DPROGRAM_SUFFIX='"$(PROGRAM_SUFFIX)"' \
		-DVERSION='"$(VER)"' \
		$(CPPFLAGS) \
		-c $^ -o $@

substitute_variables = \
	sed -s \
		-e "s:@LIBDIR@:$(LIBDIR):g" \
		-e "s:@PKGLIBDIR@:$(PKGLIBDIR):" \
		-e "s:@PROGRAM_PREFIX@:$(PROGRAM_PREFIX):" \
		-e "s:@PROGRAM_SUFFIX@:$(PROGRAM_SUFFIX):" \
		-e "s:@EARLY_PREFIX@:$(EARLY_PREFIX):" \
		-e "s:@VER@:$(VER):"

bootchartd: bootchartd.in
	$(substitute_variables) $^ > $@

bootchart-collector: $(COLLECTOR)
	$(CC) $(CFLAGS) $(LDFLAGS) -pthread -Icollector -o $@ $^

VERSION:
	@echo "$(VER)" > $@

initviz/main.py: initviz/main.py.in
	$(substitute_variables) $^ > $@

install-python: python
	install -d $(DESTDIR)$(PY_SITEDIR)/initviz
	find initviz -maxdepth 1 -name "*.py" -exec install -m 644 {} $(DESTDIR)$(PY_SITEDIR)/initviz/ \;
	install -D -m 755 initviz.py $(DESTDIR)$(BINDIR)/initviz
	[ -z "$(NO_PYTHON_COMPILE)" ] && ( cd $(DESTDIR)$(PY_SITEDIR)/initviz ; \
		$(PYTHON) $(PY_LIBDIR)/py_compile.py *.py ; \
		PYTHONOPTIMIZE=1 $(PYTHON) $(PY_LIBDIR)/py_compile.py *.py ); :

install-chroot:
	install -d $(DESTDIR)$(PKGLIBDIR)/tmpfs

install-collector: collector install-chroot
	install -m 755 -D bootchartd $(DESTDIR)$(EARLY_PREFIX)/sbin/$(PROGRAM_PREFIX)bootchartd$(PROGRAM_SUFFIX)
	install -m 644 -D bootchartd.conf $(DESTDIR)/etc/$(PROGRAM_PREFIX)bootchartd$(PROGRAM_SUFFIX).conf
	install -m 755 -D bootchart-collector $(DESTDIR)$(PKGLIBDIR)/$(PROGRAM_PREFIX)bootchart$(PROGRAM_SUFFIX)-collector

install-docs:
	install -m 644 -D README.md $(DESTDIR)$(DOCDIR)/README.md
	install -m 644 -D doc/initviz.png $(DESTDIR)$(DOCDIR)/initviz.png
	mkdir -p $(DESTDIR)$(MANDIR)
	gzip -c man/bootchartd.1 > $(DESTDIR)$(MANDIR)/$(PROGRAM_PREFIX)bootchartd$(PROGRAM_SUFFIX).1.gz
	gzip -c man/initviz.1 > $(DESTDIR)$(MANDIR)/initviz.1.gz

install: all install-python install-collector install-docs

clean:
	-rm -f bootchart-collector bootchart-collector-dynamic \
	collector/*.o initviz/main.py bootchartd VERSION

distclean: clean
	-find . -name __pycache__ -type d -exec rm -rf {} +
	-find . -name "*.o" -delete
	-find . -name "*~" -delete
	-find . -name "*.pyc" -delete
	-find . -name "*.pyo" -delete

dist:
	COMMIT_HASH=`git show-ref -s -h | head -n 1` ; \
	git archive --prefix=$(PKG_NAME)-$(VER)/ --format=tar $$COMMIT_HASH \
		| gzip -f > $(PKG_TARBALL)

test: initviz/tests
	for f in initviz/tests/*.py;\
	do \
		echo "Testing $$f...";\
		$(PYTHON) "$$f";\
	done

# PyPI packaging targets
pypi-build: python
	@echo "Building PyPI packages..."
	pyproject-build

pypi-test:
	@echo "Installing package locally for testing..."
	@echo "Run: pip install -e ."
	@echo "Or:  pip install dist/initviz-$(VER)-py3-none-any.whl"

pypi-upload-test: pypi-build
	@echo "Uploading to TestPyPI..."
	twine upload --repository testpypi dist/*

pypi-upload: pypi-build
	@echo "Uploading to PyPI..."
	@read -p "Are you sure you want to upload to PyPI? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		twine upload dist/*; \
	else \
		echo "Upload cancelled."; \
	fi

pypi-clean:
	rm -rf dist/ build/ *.egg-info/

.PHONY: all collector python clean distclean install install-chroot install-collector install-python install-docs dist test \
	pypi-build pypi-test pypi-upload-test pypi-upload pypi-clean
