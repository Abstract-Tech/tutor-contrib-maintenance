Maintenance plugin for `Tutor <https://docs.tutor.edly.io>`__
#############################################################

|pypi-badge| |ci-badge| |license-badge|

A Tutor plugin that puts a "down for maintenance" page in front of an Open
edX platform, on demand, without needing to know every domain your other
Tutor plugins have registered with Caddy.


Installation
************

.. code-block:: bash

    pip install git+https://github.com/Abstract-Tech/tutor-contrib-maintenance


How it works
************

The plugin ships a small Caddy-based static-site image (its own Caddyfile,
``maintenance.html``, and ``style.css``) that runs alongside the platform as
a ``maintenance`` service.

``tutor maintenance on`` and ``tutor maintenance off`` don't patch the main
``apps/caddy/Caddyfile`` at all. Instead they hot-swap the *running* Caddy
config through its admin API (``http://127.0.0.1:2019``, on by default
inside the ``caddy`` container):

* ``on`` replaces Caddy's routes with a single catch-all ``reverse_proxy`` to
  the ``maintenance`` container, keeping whatever ``listen`` addresses are
  already configured. Because it has no host or path matcher, it blankets
  *every* domain Caddy serves -- LMS, CMS, and any host added by any other
  plugin -- with no need to know their names, and takes effect instantly
  with no restart.
* ``off`` re-adapts ``apps/caddy/Caddyfile`` on disk and reloads that. The
  file on disk is always the source of truth, so there's no separate state
  to keep in sync.

This only applies in ``tutor local`` (production-like) mode, since that's
where Caddy fronts the platform. ``tutor dev`` mode has no Caddy -- each
service is published on its own host port -- so ``tutor maintenance on/off``
doesn't apply there; the ``maintenance`` container is still started (see
below) so you can preview the page directly.


Usage
*****

.. code-block:: bash

    tutor plugins enable maintenance
    tutor images build maintenance
    tutor images push maintenance
    tutor local launch

Toggle maintenance mode:

.. code-block:: bash

    tutor maintenance on

    # ... perform maintenance ...

    tutor maintenance off

Preview the maintenance page directly in ``tutor dev`` mode at
``http://localhost:8090`` (published by the plugin's dev docker-compose
patch, chosen to avoid clashing with the other ports Tutor's core and
bundled plugins use in dev mode).


Configuration
*************

.. list-table::
   :header-rows: 1

   * - Setting
     - Default
     - Description
   * - ``MAINTENANCE_DOCKER_IMAGE``
     - ``ghcr.io/abstract-tech/tutor-maintenance:{version}``
     - Image tag built/pulled/pushed by ``tutor images``.
   * - ``MAINTENANCE_PAGE_TITLE``
     - ``Down for maintenance``
     - ``<title>`` of the maintenance page.
   * - ``MAINTENANCE_PAGE_HEADING``
     - ``We'll be right back``
     - On-page ``<h1>``.
   * - ``MAINTENANCE_PAGE_DESCRIPTION``
     - ``This site is currently undergoing scheduled maintenance...``
     - ``<meta name="description">`` and body text.
   * - ``MAINTENANCE_FAVICON_URL``
     - ``assets/favicon.ico``
     - Favicon URL, relative to the page. Override with any URL to skip
       rebuilding the image.
   * - ``MAINTENANCE_BACKGROUND_URL``
     - ``background.jpg``
     - Background image URL, relative to ``assets/style.css``. Same
       override behavior as the favicon.

.. code-block:: bash

    tutor config save --set MAINTENANCE_PAGE_TITLE="We'll be back soon"
    tutor images build maintenance
    tutor local stop maintenance && tutor local start -d maintenance

The maintenance page's templates live at
``tutormaintenance/templates/maintenance/build/maintenance/`` --
``maintenance.html``, and its stylesheet, favicon, and background image
under ``assets/``. After editing
them (or any ``MAINTENANCE_PAGE_*`` setting), you must re-render, rebuild,
and recreate the container for the change to take effect -- a plain
``tutor local restart maintenance`` reuses the already-running container's
old image and won't pick up the rebuild.


Development
***********

.. code-block:: bash

    git clone https://github.com/Abstract-Tech/tutor-contrib-maintenance
    # Create a virtual environment and activate it
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -e ".[dev]"

License
*******

This software is licensed under the terms of the AGPLv3.


.. |ci-badge| image:: https://github.com/Abstract-Tech/tutor-contrib-maintenance/workflows/Python%20CI/badge.svg?branch=main
    :target: https://github.com/Abstract-Tech/tutor-contrib-maintenance/actions
    :alt: CI

.. |license-badge| image:: https://img.shields.io/github/license/Abstract-Tech/tutor-contrib-maintenance.svg
    :target: https://github.com/Abstract-Tech/tutor-contrib-maintenance/blob/main/LICENSE.txt
    :alt: License

.. |pypi-badge| image:: https://img.shields.io/pypi/v/tutor-contrib-maintenance.svg
    :target: https://pypi.org/project/tutor-contrib-maintenance/
    :alt: PyPI