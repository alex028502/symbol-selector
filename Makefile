GIT_HASH = "dev"

symbol-selector.deb: package/DEBIAN/control
	dpkg-deb --build package
	mv package.deb $@
package/DEBIAN/control: control package/DEBIAN FORCE
	sed "s/{ VERSION }/$(shell date +"%Y%m%d%H%M%S").$(GIT_HASH)/" $< > $@
package/DEBIAN: Makefile
	mkdir -p $@
format: venv
	$</bin/black --check .
venv: requirements.txt Makefile
	python3 -m venv $@
	$@/bin/pip install -r $<
	touch venv
FORCE:
