# zeo-plugin-ffmpeg pilot candidate

Local media probing/conversion adapter moved from zeocore. Operations in
manifest.json are existing Python method names, not Broker route identifiers,
allowlist entries or permission grants. The manifest is descriptive metadata;
zeocore does not load it. Shared contracts remain in zeocore.

This branch is preparation, not a published or installed package. Core0.24.0
contains the duplicate-registration guard but still registers ffmpeg itself.
Installing both distributions makes ffmpeg ambiguous and must refuse loading.
The core owner must remove its entry point and provide the compatibility shim
and extra in the coordinated core transition. Do not bypass that guard.

Importing the factory does not initialize the plugin. Initialization can create
an output directory and resolve media binaries; use fakes for qualification.
Binary downloads default off. No ffmpeg binaries or credentials are shipped.
The underlying ffmpeg-zeo distribution/import names are unchanged by its repo
rename to https://github.com/zeroemployeeorg/dt-ffmpeg.

Qualification still required before a pilot PR/release: approved build-backend
acquisition, wheel/sdist build and contents, clean installed entry-point
and duplicate refusal tests, fake media-operation behavior, core-owner shim/
extra smoke, license review and operator-approved release. No PyPI publication
or native media invocation is performed by this branch's metadata tests.
Hatchling1.27.0 is a proposed exact build input, not an installed/qualified tool.
