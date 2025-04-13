PYTHON_SITE_PACKAGES := $(shell python3 -c "import site; print(site.getsitepackages()[0].replace('lib64', 'lib'))")
TARGET_DIR := $(DESTDIR)$(PYTHON_SITE_PACKAGES)/flatpost
BIN_DIR := $(DESTDIR)/usr/bin
DESKTOP_DIR := $(DESTDIR)/usr/share/applications
DATA_DIR := $(DESTDIR)/usr/share/flatpost
ICON_DIR := $(DESTDIR)/usr/share/icons/hicolor/1024x1024/apps
LICENSE_DIR := $(DESTDIR)/usr/share/licenses/flatpost

.PHONY: all install clean

all: install

install:
	@echo "Installing Python files to $(TARGET_DIR)"
	mkdir -p $(TARGET_DIR)
	install -m 644 src/fp_turbo.py $(TARGET_DIR)/fp_turbo.py

	@echo "Main executable file to $(BIN_DIR)"
	mkdir -p $(BIN_DIR)
	install -m 755 src/flatpost.py $(BIN_DIR)/flatpost

	@echo "Installing desktop file to $(DESKTOP_DIR)"
	mkdir -p $(DESKTOP_DIR)
	install -m 644 data/usr/share/applications/com.flatpost.flatpostapp.desktop $(DESKTOP_DIR)/com.flatpost.flatpostapp.desktop

	@echo "Installing data files to $(DATA_DIR)"
	mkdir -p $(DATA_DIR)
	install -m 644 data/usr/share/flatpost/collections_data.json $(DATA_DIR)/collections_data.json

	@echo "Installing icon file to $(ICON_DIR)"
	mkdir -p $(ICON_DIR)
	install -m 644 data/usr/share/icons/hicolor/1024x1024/apps/com.flatpost.flatpostapp.png $(ICON_DIR)/com.flatpost.flatpostapp.png

	@echo "Installing license file to $(LICENSE_DIR)"
	mkdir -p $(LICENSE_DIR)
	install -m 644 data/usr/share/licenses/flatpost/LICENSE $(LICENSE_DIR)/LICENSE

clean:
	@echo "Cleaning up installed files"
	rm -rf $(TARGET_DIR)
	rm -f $(BIN_DIR)/flatpost
	rm -f $(DESKTOP_DIR)/com.flatpost.flatpostapp.desktop
	rm -f $(DATA_DIR)/collections_data.json
	rm -f $(ICON_DIR)/com.flatpost.flatpostapp.png
	rm -f $(LICENSE_DIR)/com.flatpost.flatpostapp.png
