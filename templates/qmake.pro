TEMPLATE=app
CONFIG+=console
CONFIG-=app_bundle
CONFIG-=qt

HOME=$$(HOME)

exists(PRIFILE_PLACEHOLDER) {
    include(PRIFILE_PLACEHOLDER)
}

TARGET = TARGET_PLACEHOLDER

MAKEFILE = MAKEFILE_PLACEHOLDER

DEFINES += \
	DEFINES_PLACEHOLDER

OTHER_FILES += \
	OTHER_FILES_PLACEHOLDER

HEADERS += \
	HEADERS_PLACEHOLDER

SOURCES += \
	SOURCES_PLACEHOLDER

INCLUDEPATH += \
	INCLUDEPATH_PLACEHOLDER
