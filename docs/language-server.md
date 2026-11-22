# Language Server

`fire-ls` reports FIRE validation errors in your editor while you type. It
currently publishes diagnostics for requirement documents (`.sysreq.md`,
`.swreq.md`, `.regreq.md` and custom suffixes from `fire_config.yaml`). See
[the design](design/language-server.md) for what is planned.

## Running

Build the server from this repository and start it on stdio:

```bash
bazel build //fire/lsp:fire_ls
bazel-bin/fire/lsp/fire_ls [--config path/to/fire_config.yaml]
```

Without Bazel, install the pinned packages from `requirements.txt` and run
`python -m fire.lsp` with the repository root on `PYTHONPATH`.

## Neovim (0.11+)

```lua
vim.lsp.config("fire_ls", {
  cmd = { "/absolute/path/to/fire/bazel-bin/fire/lsp/fire_ls" },
  filetypes = { "markdown" },
  root_markers = { "MODULE.bazel" },
})
vim.lsp.enable("fire_ls")
```

Documents whose file name does not end in a configured document-type suffix are
ignored, so other Markdown files are unaffected.

## Diagnostics

| Code      | Meaning                                    |
| --------- | ------------------------------------------ |
| `FIRE001` | Heading is not a valid requirement ID      |
| `FIRE002` | Duplicate requirement ID                   |
| `FIRE003` | Requirement has no metadata line           |
| `FIRE004` | Bare or malformed `TODO`                   |
| `FIRE005` | Invalid metadata field value               |
| `FIRE006` | Missing required metadata field            |
| `FIRE007` | Unknown metadata field                     |
| `FIRE008` | `Parent` entry is not a link or `TODO(..)` |
