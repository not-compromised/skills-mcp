# Shot Page

Share captioned screenshots and short recordings through a temporary private link.
The package includes an agent skill, a Python helper, and Tailscale Serve setup.
No MCP server, custom domain, Docker container, or application service is needed.

This is a portable adaptation of the Shot Page workflow developed in this project's
maintainer's tools repository. It is covered by this repository's MIT license.
The public helper replaces the original machine-specific Caddy integration.

## Install for your CLI

Requires Linux, Python 3, and Tailscale installed and signed in on the hosting machine.
The viewing device must also have tailnet access. Install optional FFmpeg for video
frame extraction. On Omarchy, `omarchy pkg add python tailscale ffmpeg` installs the
packages; complete Tailscale sign-in using its normal setup process.

From the repository root:

```sh
python3 install-skill.py shot-page --client codex
# Or:
python3 install-skill.py shot-page --client claude
```

The installer refuses an existing skill. Keep the checkout in place and restart the
CLI. Invoke `$shot-page` in Codex or `/shot-page` in Claude Code with the work to show.
The skill can also be selected automatically for a matching request.

## Configure private hosting once

[Tailscale Serve](https://tailscale.com/docs/reference/tailscale-cli/serve) serves a
local directory over HTTPS inside your tailnet. Enable MagicDNS and HTTPS as directed
by Tailscale. Tailnet access rules control the audience; pages have no separate login.
Restrict access to the host and chosen port to the intended viewers. Do not enable
Funnel for this endpoint.

First inspect existing hosting, including any Funnel configuration:

```sh
tailscale serve status
tailscale funnel status
tailscale status --json
```

Choose an unused HTTPS port. The examples use 8443. If that port is occupied or
publicly exposed, choose another unused port. Do not replace another application's
endpoint, run `serve reset`, or restart Tailscale. Existing T3 hosting often uses 443.
Use `Self.DNSName` from the status output as the hostname, dropping its trailing dot.

Initialize local storage with your actual hostname:

```sh
python3 packages/shot-page/skill/scripts/shot-page.py init \
  --base-url https://your-host.your-tailnet.ts.net:8443
```

This creates `~/.local/share/shot-page` with private permissions. `staged` holds drafts,
`public` holds published pages, and `retained` holds copies awaiting verified cleanup.
The directory is outside the repository, so screenshots and runtime state do not
enter Git history. Never put unrelated files or symbolic links inside it.

After confirming the selected port is unused, enable only this endpoint:

```sh
tailscale serve --bg --https=8443 "$HOME/.local/share/shot-page/public"
```

Run that command in your terminal so any required Tailscale setup prompt is visible.
If your installation requires administrator privileges, use its documented operator
or sudo setup. The package does not change those privileges. The background Serve
configuration persists across reboots; individual pages remain until removed.
Confirm the printed URL opens from the viewing device before relying on it.

## Use

Use your browser or desktop capture tool to create images or MP4 recordings. Inspect
them before sharing. The helper does not launch desktops or capture your screen.

```sh
python3 packages/shot-page/skill/scripts/shot-page.py add dialog-change /tmp/before.png /tmp/after.png
```

Write `index.html` into the printed staging directory. Keep the page self-contained,
with captions, responsive images linking to their originals, and inline video controls.
Then publish:

```sh
python3 packages/shot-page/skill/scripts/shot-page.py publish dialog-change
python3 packages/shot-page/skill/scripts/shot-page.py list
```

Publication moves the prepared directory into the served directory, then checks the
HTML over HTTPS. A failed response or content mismatch withdraws it back to staging.
A failed attempt may have been briefly reachable. Published names cannot be replaced;
use a new name when updating a review. Files inside the private storage directory
must only be managed by trusted processes running as your user.

For a recording, extract six sample frames into a new directory and inspect them:

```sh
python3 packages/shot-page/skill/scripts/shot-page.py frames /tmp/interaction.mp4 /tmp/interaction-frames
```

The viewer can download any file in a published page. Review the whole page directory,
including HTML and CSS, for unintended content. Sampling frames verifies visible
behavior but cannot rule out a one-frame disclosure in a recording.

After the user agrees to take a page down:

```sh
python3 packages/shot-page/skill/scripts/shot-page.py remove dialog-change
```

Removal withdraws the directory, checks for HTTP 404, then deletes its retained copy.
If that check fails, the command prints the retained path and exits unsuccessfully.
Check the endpoint and confirm the page URL returns 404 before manually deleting
that exact retained directory. Downloaded copies and browser caches cannot be revoked.

## T3 Code

Install the skill under the account running T3's selected agent provider, then open
a fresh provider session. Setup and helper commands run on the hosting machine.
If the provider runs elsewhere, transfer only the intended page assets to that host
and invoke the helper there. Keep the phone connected to Tailscale to open the link.
This package does not change T3 settings, restart its server, or use its hosting port.

## Remove the integration

List the pages and arrange their removal first. Confirm 8443 is still your Shot Page
endpoint, then disable only that endpoint with `tailscale serve --https=8443 off`.
Use the port you selected if different. Verify other services remain configured.
Inspect and unlink the installed skill symlink. Retain storage until all failed-cleanup
copies have been reviewed; never delete a whole directory just because it is old.

## Verification

Run the repository's `./test`. Shot Page's tests exercise staging, serving, publication,
rollback, cross-page preservation, and withdrawal through a real HTTP server inside
the isolated test network. They do not change the host's Tailscale configuration.
Live Tailscale HTTPS access must be checked during setup on the destination machine.
