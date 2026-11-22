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

| Code      | Meaning                                                  |
| --------- | -------------------------------------------------------- |
| `FIRE001` | Heading is not a valid requirement ID                    |
| `FIRE002` | Duplicate requirement ID                                 |
| `FIRE003` | Requirement has no metadata line                         |
| `FIRE004` | Bare or malformed `TODO`                                 |
| `FIRE005` | Invalid metadata field value                             |
| `FIRE006` | Missing required metadata field                          |
| `FIRE007` | Unknown metadata field                                   |
| `FIRE008` | `Parent` entry is not a link or `TODO(..)`               |
| `FIRE009` | Reference path is not repository-relative                |
| `FIRE010` | Reference is missing `?version=N`                        |
| `FIRE011` | Parameter link text does not match its anchor            |
| `FIRE012` | Linked file does not exist                               |
| `FIRE013` | Linked requirement ID or parameter not found in the file |
| `FIRE014` | Link points at a version newer than the file has         |
| `FIRE015` | Link points at an older version than the file has        |

Links are resolved against the nearest ancestor directory that contains a
`MODULE.bazel` or `WORKSPACE` file; without one only the syntax checks run.
Open documents are re-checked whenever another open document changes, using
its unsaved content, and when a Markdown or YAML file changes on disk (the
client must support dynamic file watching, which Neovim does).
`FIRE014` is an error for parameters and a warning for requirements, matching
the build. `FIRE015` is always a warning.
