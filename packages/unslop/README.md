# Unslop

A writing-editing skill by **Lauren Tan**, from the [pstack plugin in cursor/plugins](https://github.com/cursor/plugins/tree/main/pstack/skills/unslop). It identifies inflated claims, canned phrasing, repetitive structure, and other AI writing habits.

## Source and attribution

`skill/SKILL.md` is an unchanged copy from upstream revision [`93b00b89`](https://github.com/cursor/plugins/tree/93b00b89ef425a9c1bac0d0b317dfc49c930ac99/pstack/skills/unslop). [LICENSE](skill/LICENSE) is the original MIT license, including Lauren Tan's copyright notice. [upstream.json](upstream.json) records the repository, exact revision, source paths, and SHA-256 hashes.

This is a vendored snapshot inside a collection, not a GitHub fork of the entire Cursor plugin marketplace. Its origin is recorded explicitly; changes to the upstream skill should be proposed in `cursor/plugins`.

The only runtime addition is `skill/agents/openai.yaml`, which carries upstream's manual-invocation policy into Codex. The original frontmatter includes `disable-model-invocation: true`; that setting is preserved. The description's “Must always apply” wording is upstream text, not an installer change to your global agent instructions.

## Install for your CLI

From the `skills-mcp` repository root:

```sh
python3 install-skill.py unslop --client codex
```

Or for Claude Code:

```sh
python3 install-skill.py unslop --client claude
```

The installer creates a symlink under the selected client's skills directory. It respects `CODEX_HOME` or `CLAUDE_CONFIG_DIR` when set, refuses existing foreign files or links, and makes no changes to your currently installed Unslop skill. Keep this checkout in place while using the link.

Restart the CLI, then invoke `$unslop` in Codex or `/unslop` in Claude Code with the text you want edited. This package needs no MCP, service, API key, or desktop configuration.

## T3 Code

Run the same installer on the machine hosting T3's agent provider, under that provider's user. Open a fresh provider session so it discovers the skill. If the T3 composer does not offer the command, ask the provider to use the installed Unslop skill by name. No token export or desktop setup is required.

## Update and remove

To update, review changes to the [upstream skill](https://github.com/cursor/plugins/commits/main/pstack/skills/unslop/SKILL.md) and its license. Import both from one chosen commit and update `upstream.json` together. Keep the upstream files unchanged; document any compatibility additions separately. `./test` verifies the recorded hashes.

To remove the integration, unlink the installed `unslop` symlink after checking that it still points to this package. Removing that link preserves both this package and any separate installation.
