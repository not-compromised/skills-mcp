---
name: shot-page
description: Share captioned screenshots or short recordings on a temporary private page when the user asks to see visual work, then arrange its removal.
---

# Shot Page

Use a temporary page when screenshots or a short recording can show the result.
If the user needs to operate a form or application, provide an interactive preview
instead. Publishing a page does not authorize changing the application it shows.

Run the bundled helper with Python 3. Resolve `scripts/shot-page.py` relative to
this skill's directory. Run it on the host configured to serve the pages.

## Capture and explain

Use the available browser or desktop capture tool. On Wayland, use a tool that
supports Wayland or the agent's isolated desktop. Never assume an X11 display.
Announce live desktop activity to the user and capture only the intended window.
Do not start, restart, or stop the user's desktop or transport to obtain a shot.

Inspect every image before publishing. Look for credentials, private notifications,
and unrelated personal information. Keep enough surrounding context to understand
the result; add a detail crop when needed, keeping the full image too. Do not trim
black pixels automatically, since they may be part of the content.

For motion, make a short MP4 recording of one behavior. Show the cursor driving
clicks and the resulting state. Use the capture tool's own recording controls.
Before sharing, run `frames VIDEO OUTPUT_DIRECTORY`, inspect the extracted stills,
and confirm the depicted change. Sampled frames cannot prove a recording contains
no brief secret exposure; record a controlled scene and discard a compromised clip.
Pair the video with a still so the result can be skimmed without playback.

## Prepare and publish

1. Run `add NAME FILE...`. It copies explicit files into a private staging directory
   and prints where to write `index.html`. Choose a name for the change being shown.
2. Write a self-contained page with a viewport meta tag and no external assets.
   Use one figure per image or clip, with a caption saying what to inspect. Link
   images to themselves for full-size viewing. Use `max-width:100%; height:auto`
   for media. Videos need `controls muted playsinline preload="metadata"`.
3. Say the page is temporary and can be removed on request. Include before/after
   evidence when comparing changes. Caption only what you verified.
4. Run `publish NAME`. Publication checks the served HTML against the staged HTML;
   if the check fails, the helper withdraws the page and reports the failure.
5. Give the verified URL as a tappable link in your response. A local file path or
   successful upload alone does not prove the user can reach it. Ask the user to
   check it if their device's tailnet access has not been established.

A published name is immutable. Use a new name for a revision, and arrange removal
of the old page. This prevents a second agent from silently replacing a live review.

## Cleanup

When the user finishes reviewing or the session wraps up, ask whether to remove
the page or keep it available. Do not treat silence as consent.

After approval, run `remove NAME`. The helper withdraws the directory and checks
for HTTP 404 before deleting its retained copy. If verification fails, report the
retained path and the failed check; do not claim cleanup is complete.

Use `list` to see staged, published, and retained pages. Do not remove another
agent's page or an old page solely because it looks abandoned.

## Setup boundaries

Read the [package setup guide](../README.md) before first use. The helper needs its configured
private host and a page directory outside version control. Pages must stay within
the tailnet. Do not use Funnel, a public tunnel, or public hosting. Tailnet access
rules determine who can see them; a hard-to-guess URL is not access control.

No MCP server is required. The same commands work from an agent CLI or a T3 provider
running under the configured user's account. If hosting is on another machine,
copy only the intended assets there and run the helper there.
