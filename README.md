# skills-mcp

Agent skills, MCP servers, and the configuration needed to run them.

The first package is **agent-desktop**: on-demand Hyprland desktops that agents can use for browser and GUI work while your current window keeps focus. It includes the MCP server, CLI helper, skill, nested desktop configuration, and per-user installer.

## Install agent-desktop

Requires Linux, a running Hyprland session with Lua configuration, and systemd user services. The package was tested on Hyprland 0.56.2. On Omarchy, install dependencies from a terminal:

```sh
omarchy pkg add nodejs npm python jq grim wtype wlrctl xorg-xwayland
```

Clone the repository and install as your regular user:

```sh
git clone https://github.com/not-compromised/skills-mcp.git
cd skills-mcp
python3 packages/agent-desktop/install.py
```

To choose a monitor, get its output name from `hyprctl monitors`, then pass it to the installer:

```sh
python3 packages/agent-desktop/install.py --monitor DP-1
```

Restart your Claude Code or Codex CLI and ask it to use the agent-desktop skill. The skill can call the local MCP through `agent-desktop tool` without native MCP registration. New desktop windows do not take initial focus; click one to interact with it yourself.

The MCP listens on loopback and requires a private token. Desktop input and browser profiles are separate, but commands still run with your user’s filesystem permissions. This is not a security sandbox.

See the [package guide](packages/agent-desktop/README.md) for optional native MCP registration, operation, removal, and [T3 Code integration](packages/agent-desktop/README.md#t3-code-integration). Direct CLI use is the default documented setup.

## Omarchy contribution

The same package was submitted in [Omarchy PR #10594](https://github.com/omacom/omarchy/pull/10594). That PR also adds `omarchy install ai agent-desktop` and the Omarchy manual entry. The command is proposed upstream; use the standalone installer here until your installed Omarchy version includes it.

The initial export matches `default/agent-desktop` in that PR’s commit `579ee99`. The Omarchy integration wrapper and manual entry belong to that repository.

## Test

Install Bubblewrap for test isolation, then run:

```sh
./test
```

The runner installs locked npm dependencies with lifecycle scripts disabled, then runs the package tests in a separate process and network namespace. It supplies a temporary home and no host desktop sockets, session bus, or GPU devices. Tests cover the actual HTTP authentication, client calls, desktop ownership/lifecycle behavior, and installer preservation/rollback.

Do not use the broad Omarchy test suite as a live-session smoke test. GUI verification belongs in a disposable graphical environment.

## License

[MIT](LICENSE).
