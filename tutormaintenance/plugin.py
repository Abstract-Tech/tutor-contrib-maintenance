import os
from glob import glob

import click
import importlib_resources
from tutor import config as tutor_config
from tutor import hooks
from tutor.commands.context import Context
from tutor.commands.local import LocalContext

from .__about__ import __version__

########################################
# CONFIGURATION
########################################

hooks.Filters.CONFIG_DEFAULTS.add_items(
    [
        # Add your new settings that have default values here.
        # Each new setting is a pair: (setting_name, default_value).
        # Prefix your setting names with 'MAINTENANCE_'.
        ("MAINTENANCE_VERSION", __version__),
        (
            "MAINTENANCE_DOCKER_IMAGE",
            "ghcr.io/abstract-tech/tutor-maintenance:{{ MAINTENANCE_VERSION }}",
        ),
        # Customize the maintenance page's <title>, <meta name="description">,
        # and on-page heading.
        ("MAINTENANCE_PAGE_TITLE", "Down for maintenance"),
        ("MAINTENANCE_PAGE_HEADING", "We'll be right back"),
        (
            "MAINTENANCE_PAGE_DESCRIPTION",
            "This site is currently undergoing scheduled maintenance. Please check back shortly.",
        ),
        # Favicon and background image. Default to the images bundled in the
        # maintenance image itself; override with any URL (e.g. a CDN-hosted
        # image) to skip rebuilding the image just to change them. Root-
        # relative by default since the maintenance page is served for
        # every request path (caddy's try_files falls back to it without a
        # redirect), so a path-relative URL would resolve against whatever
        # page the visitor was on instead of the maintenance image.
        ("MAINTENANCE_FAVICON_URL", "/assets/favicon.ico"),
        # Relative to the stylesheet (assets/style.css), unlike the favicon
        # URL above which is relative to the page; both default to pointing
        # at the same bundled image.
        ("MAINTENANCE_BACKGROUND_URL", "background.jpg"),
    ]
)

hooks.Filters.CONFIG_UNIQUE.add_items(
    [
        # Add settings that don't have a reasonable default for all users here.
        # For instance: passwords, secret keys, etc.
        # Each new setting is a pair: (setting_name, unique_generated_value).
        # Prefix your setting names with 'MAINTENANCE_'.
        # For example:
        ### ("MAINTENANCE_SECRET_KEY", "{{ 24|random_string }}"),
    ]
)

hooks.Filters.CONFIG_OVERRIDES.add_items(
    [
        # Danger zone!
        # Add values to override settings from Tutor core or other plugins here.
        # Each override is a pair: (setting_name, new_value). For example:
        ### ("PLATFORM_NAME", "My platform"),
    ]
)


########################################
# INITIALIZATION TASKS
########################################

# To add a custom initialization task, create a bash script template under:
# tutormaintenance/templates/maintenance/tasks/
# and then add it to the MY_INIT_TASKS list. Each task is in the format:
# ("<service>", ("<path>", "<to>", "<script>", "<template>"))
MY_INIT_TASKS: list[tuple[str, tuple[str, ...]]] = [
    # For example, to add LMS initialization steps, you could add the script template at:
    # tutormaintenance/templates/maintenance/tasks/lms/init.sh
    # And then add the line:
    ### ("lms", ("maintenance", "tasks", "lms", "init.sh")),
]


# For each task added to MY_INIT_TASKS, we load the task template
# and add it to the CLI_DO_INIT_TASKS filter, which tells Tutor to
# run it as part of the `init` job.
for service, template_path in MY_INIT_TASKS:
    full_path: str = str(
        importlib_resources.files("tutormaintenance")
        / os.path.join("templates", *template_path)
    )
    with open(full_path, encoding="utf-8") as init_task_file:
        init_task: str = init_task_file.read()
    hooks.Filters.CLI_DO_INIT_TASKS.add_item((service, init_task))


########################################
# DOCKER IMAGE MANAGEMENT
########################################


# Images to be built by `tutor images build`.
# Each item is a quadruple in the form:
#     ("<tutor_image_name>", ("path", "to", "build", "dir"), "<docker_image_tag>", "<build_args>")
hooks.Filters.IMAGES_BUILD.add_items(
    [
        (
            "maintenance",
            ("plugins", "maintenance", "build", "maintenance"),
            "{{ MAINTENANCE_DOCKER_IMAGE }}",
            (),
        ),
    ]
)


# Images to be pulled as part of `tutor images pull`.
# Each item is a pair in the form:
#     ("<tutor_image_name>", "<docker_image_tag>")
hooks.Filters.IMAGES_PULL.add_items(
    [
        ("maintenance", "{{ MAINTENANCE_DOCKER_IMAGE }}"),
    ]
)


# Images to be pushed as part of `tutor images push`.
# Each item is a pair in the form:
#     ("<tutor_image_name>", "<docker_image_tag>")
hooks.Filters.IMAGES_PUSH.add_items(
    [
        ("maintenance", "{{ MAINTENANCE_DOCKER_IMAGE }}"),
    ]
)


########################################
# TEMPLATE RENDERING
# (It is safe & recommended to leave
#  this section as-is :)
########################################

hooks.Filters.ENV_TEMPLATE_ROOTS.add_items(
    # Root paths for template files, relative to the project root.
    [
        str(importlib_resources.files("tutormaintenance") / "templates"),
    ]
)

hooks.Filters.ENV_TEMPLATE_TARGETS.add_items(
    # For each pair (source_path, destination_path):
    # templates at ``source_path`` (relative to your ENV_TEMPLATE_ROOTS) will be
    # rendered to ``source_path/destination_path`` (relative to your Tutor environment).
    # For example, ``tutormaintenance/templates/maintenance/build``
    # will be rendered to ``$(tutor config printroot)/env/plugins/maintenance/build``.
    [
        ("maintenance/build", "plugins"),
    ],
)


########################################
# PATCH LOADING
# (It is safe & recommended to leave
#  this section as-is :)
########################################

# For each file in tutormaintenance/patches,
# apply a patch based on the file's name and contents.
for path in glob(str(importlib_resources.files("tutormaintenance") / "patches" / "*")):
    with open(path, encoding="utf-8") as patch_file:
        hooks.Filters.ENV_PATCHES.add_item((os.path.basename(path), patch_file.read()))


########################################
# CUSTOM JOBS (a.k.a. "do-commands")
########################################

# A job is a set of tasks, each of which run inside a certain container.
# Jobs are invoked using the `do` command, for example: `tutor local do importdemocourse`.
# A few jobs are built in to Tutor, such as `init` and `createuser`.
# You can also add your own custom jobs:


# To add a custom job, define a Click command that returns a list of tasks,
# where each task is a pair in the form ("<service>", "<shell_command>").
# For example:
### @click.command()
### @click.option("-n", "--name", default="plugin developer")
### def say_hi(name: str) -> list[tuple[str, str]]:
###     """
###     An example job that just prints 'hello' from within both LMS and CMS.
###     """
###     return [
###         ("lms", f"echo 'Hello from LMS, {name}!'"),
###         ("cms", f"echo 'Hello from CMS, {name}!'"),
###     ]


# Then, add the command function to CLI_DO_COMMANDS:
## hooks.Filters.CLI_DO_COMMANDS.add_item(say_hi)

# Now, you can run your job like this:
#   $ tutor local do say-hi --name="John Doe"


#######################################
# CUSTOM CLI COMMANDS
#######################################

# `tutor maintenance on` / `tutor maintenance off` hot-swap the *running*
# Caddy config via its admin API (http://127.0.0.1:2019, enabled by default
# inside the caddy container). This bypasses the Caddyfile entirely, so it
# blankets every host caddy serves -- LMS, CMS, and any domain added by any
# other plugin -- with no need to know their names, and takes effect
# instantly with no restart.
#
# "on" inserts a single terminal catch-all reverse_proxy route in FRONT of
# the srv0 server's existing routes, via a targeted PUT to routes/0 -- it
# does not touch or replace the existing routes.
#
# The existing routes must be left alone because Caddy's automatic HTTPS
# re-provisions the server's TLS connection policies from the *current*
# routes on every config change: it scans each route's host matcher to know
# which domain to select a certificate for. Replace the routes array with a
# matcher-less catch-all (whether via /load or a targeted PATCH to `routes`)
# and that scan comes up empty, so Caddy installs a TLS policy with no
# certificate for the domain -- the handshake fails with
# ERR_SSL_PROTOCOL_ERROR. Invisible locally on plain HTTP; fatal in
# production behind real certs. Inserting ahead of the existing routes
# instead keeps their host matchers in place for that scan, while still
# winning every request first because it's marked terminal.
#
# "off" just re-adapts the Caddyfile on disk and reloads that in full, which
# is always the source of truth (and never had the inserted route), so no
# state needs to be saved or removed.

_MAINTENANCE_ON_SCRIPT = """set -e
printf '{"handle":[{"handler":"reverse_proxy","upstreams":[{"dial":"maintenance:80"}]}],"terminal":true}' \\
    > /tmp/tutor-maintenance-on.json
curl -sf -X PUT -H 'Content-Type: application/json' \\
    --data @/tmp/tutor-maintenance-on.json \\
    http://127.0.0.1:2019/config/apps/http/servers/srv0/routes/0
"""

_MAINTENANCE_OFF_SCRIPT = """set -e
caddy adapt --config /etc/caddy/Caddyfile --adapter caddyfile --pretty=false \\
    > /tmp/tutor-maintenance-off.json
wget -qO- --header='Content-Type: application/json' \\
    --post-file=/tmp/tutor-maintenance-off.json http://127.0.0.1:2019/load
"""


def _exec_in_caddy(root: str, script: str) -> None:
    config = tutor_config.load(root)
    runner = LocalContext(root).job_runner(config)
    runner.docker_compose("exec", "caddy", "sh", "-c", script)


@click.group()
def maintenance() -> None:
    """
    Manage maintenance mode.
    """


@maintenance.command(name="on")
@click.pass_obj
def maintenance_on(context: Context) -> None:
    """
    Route all traffic, for every domain caddy serves, to the maintenance page.
    """
    _exec_in_caddy(context.root, _MAINTENANCE_ON_SCRIPT)


@maintenance.command(name="off")
@click.pass_obj
def maintenance_off(context: Context) -> None:
    """
    Restore normal routing.
    """
    _exec_in_caddy(context.root, _MAINTENANCE_OFF_SCRIPT)


hooks.Filters.CLI_COMMANDS.add_item(maintenance)


# This allows you to run:
#   $ tutor maintenance on
#   $ tutor maintenance off
