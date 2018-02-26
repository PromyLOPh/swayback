swayback
========

This is a proof of concept for Service Worker-based web app replay, similar to
archive.org’s Wayback Machine.

Rationale
---------

Traditionally replaying websites relied heavily on rewriting URL’s in static
HTML pages to adapt them to a new origin and path hierarchy (i.e.
``https://web.archive.org/web/<date>/<url>``). With the rise of web apps, which
load their content dynamically, this is no longer sufficient.

Instagram is an example for this: User’s profiles dynamically load content to
implement “infinite scrolling”. The corresponding request is a GraphQL query,
which returns JSON-encoded data with an application-defined structure.  This
response includes URL’s to images, which must be rewritten as well, in order
for replay to work correctly. So the replay software needs to parse and rewrite
JSON as well as HTML.

However, this response could have used an arbitrary serialization format and
may contain relative URL’s or just values used in a URL template. Both are
more difficult to spot than absolute URL’s. This makes server-side rewriting
difficult and cumbersome, perhaps even impossible.

Implementation
--------------

Instead swayback relies on a new web technology called *Service Workers*. These
can be installed for a given domain and path prefix. They basically act as a
proxy between the browser and server, allowing them to intercept and rewrite
any request a web app makes. This is exactly what is needed to properly replay
archived web apps.

swayback provides an HTTP server, responing to queries for the wildcard
domain ``*.swayback.localhost``. The page served first installs a service
worker and then reloads the page. Now the service worker is in control of
network requests and rewrites a request like (for instance)
``www.instagram.com.swayback.localhost:5000/bluebellwooi/`` to
``swayback.localhost:5000/raw`` with the real URL in the POST request body.
swayback’s server looks up that URL in the WARC files provided and replies
with the original server’s response, which is then returned by the service
worker to the browser without modification.

Usage
-----

Since this is a proof of concept functionality is quite limited. You’ll need
the following python packages:

- flask
- warcio

swayback uses the hardcoded domain ``swayback.localhost``, which means you need
to set up your DNS resolver accordingly. An example for unbound looks like
this:

.. code:: unbound

    local-zone: "swayback.localhost." redirect
    local-data: "swayback.localhost. 30 IN A 127.0.0.1"

After you recorded some WARCs move them into swayback’s base directory and run:

.. code:: bash

    export FLASK_APP=swayback/__init__.py
    export FLASK_DEBUG=1
    flask run --with-threads

Then navigate to http://swayback.localhost:5000, which (hopefully) lists all
HTML pages found in those WARC files.

Caveats
-------

- Hardcoded replay domain
- URL lookup is broken, only HTTPS sites work correctly

Related projects
----------------

This approach complements efforts such as crocoite_, a web crawler based on
Google Chrome.

Reconstructive_/ipwb_
    Uses Sevice Worker to intercept and rewrite requests. Relies on Referer
    header. Rewrites links inside HTML pages using Regular Expressions before
    passing them to the browser. See `Client-side Reconstruction of Composite
    Mementos Using ServiceWorker`__.

    __ http://www.cs.odu.edu/%7Emkelly/papers/2017_jcdl_serviceWorker.pdf
pywb_
    Uses `rewrite modules`_ to alter URLs in HTML pages/JSON
    responses/cookies/…

.. _rewrite modules: https://github.com/webrecorder/pywb/tree/master/pywb/rewrite
.. _pywb: https://github.com/webrecorder/pywb/
.. _crocoite: https://github.com/PromyLOPh/crocoite
.. _Reconstructive: https://github.com/oduwsdl/Reconstructive/
.. _ipwb: https://github.com/oduwsdl/ipwb/

