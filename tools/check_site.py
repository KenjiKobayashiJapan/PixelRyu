#!/usr/bin/env python3
"""Pre-deploy sanity checks for the PixelRyu site (run before every push).

It exists to stop the #1 deploy regression we have actually hit:
a sub-page whose app slug is NOT registered in breadcrumb.js APP_NAMES,
which makes breadcrumb.js bail out (detect() -> null) and render NO
breadcrumb at all — silently. See DEPLOY.md.

Checks
  1. breadcrumb: every app sub-page that includes breadcrumb.js must have
     its slug registered in breadcrumb.js APP_NAMES (else breadcrumb is
     missing on that page).                                      -> ERROR
  2. breadcrumb: pages of a registered app that forgot the include. -> WARN
  3. cache: every breadcrumb.js / video reference carries a ?v=.    -> WARN

Usage:  python3 tools/check_site.py          (from the PixelRyu repo root)
Exit code 1 if any ERROR, else 0.
"""
import glob
import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def rel(path):
    return os.path.relpath(path, ROOT)


errors, warns = [], []

# Slugs registered in breadcrumb.js APP_NAMES (e.g. "tatami": { all: "TATAMI" }).
breadcrumb = read(os.path.join(ROOT, "breadcrumb.js"))
registered = set(re.findall(r'"([a-z0-9-]+)":\s*\{\s*all:', breadcrumb))

# Every directory one level below the root that has an index.html is an app page.
app_dirs = sorted({os.path.dirname(p) for p in glob.glob(os.path.join(ROOT, "*", "index.html"))})

for d in app_dirs:
    slug = os.path.basename(d)
    pages = sorted(glob.glob(os.path.join(d, "*.html")))
    with_bc = [p for p in pages if "breadcrumb.js" in read(p)]
    without_bc = [p for p in pages if "breadcrumb.js" not in read(p)]

    # (1) breadcrumb present in markup but slug not registered -> renders nothing.
    if with_bc and slug not in registered:
        errors.append(
            "[breadcrumb] app '%s' is NOT in breadcrumb.js APP_NAMES -> breadcrumb will NOT render on: %s"
            % (slug, ", ".join(rel(p) for p in with_bc))
        )

    # (2) a registered app whose some pages forgot the include.
    if slug in registered and without_bc:
        warns.append(
            "[breadcrumb] app '%s' pages missing the breadcrumb.js <script>: %s"
            % (slug, ", ".join(rel(p) for p in without_bc))
        )

    # (3) cache-busting: breadcrumb.js / .mp4 refs should all carry ?v=.
    for p in pages:
        html = read(p)
        for m in re.finditer(r'(breadcrumb\.js|[\w./-]+\.mp4)(\?v=\d+)?', html):
            if m.group(1).endswith((".js", ".mp4")) and not m.group(2):
                warns.append("[cache] %s references %s without ?v=" % (rel(p), m.group(1)))

if warns:
    print("\n".join("WARN  " + w for w in sorted(set(warns))))
if errors:
    print("\n".join("ERROR " + e for e in errors))

print("\n%d app page(s) checked. Registered in breadcrumb.js: %s" % (len(app_dirs), ", ".join(sorted(registered))))
if errors:
    print("\nFAIL: %d breadcrumb error(s) — fix before deploying." % len(errors))
    sys.exit(1)
print("\nOK: breadcrumb registration is consistent.")
