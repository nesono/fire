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
  filetypes = { "markdown", "yaml" },
  root_markers = { "MODULE.bazel" },
})
vim.lsp.enable("fire_ls")
```

`"yaml"` is only needed for parameter files, see below.

Documents whose file name does not end in a configured document-type suffix are
ignored, so other Markdown files are unaffected.

## Link styles

Inline links (`[text](url)`) and reference-style links (`[text][1]`, `[text][]`
and `[text]` with a `[1]: url` definition) are understood by every feature.
For a reference-style link, problems with the target (path, version, missing
file, stale version) are reported at the definition line, once per definition,
while the label and text rules apply at the usage. A `[text]` without a
definition is plain text; `[REQ-ID][label]` or `[@name][label]` with an
undefined label is reported as `FIRE016`. Go to definition and find references
work from the usage of a reference-style link, but not yet from its definition
line.

## Go to definition

On a parameter or requirement link, go to definition jumps to the linked
`name_vN` key or requirement heading. If the exact version is not defined, it
jumps to the latest one; if the file exists but the ID or parameter does not, it
jumps to the top of the file. In Neovim use `vim.lsp.buf.definition()` or
`<C-]>`. Unsaved buffers are preferred over files on disk.

## Completion

In a requirement document the metadata line under a requirement heading is
completed: field names of the document type (required fields first, fields
already present left out) and, after `Key:`, the allowed values (enum values,
`true`/`false`) and a `TODO(KEY-1234)` snippet where the field allows a TODO.
Inside the URL of a link (`[text](url)` or a `[label]: url` definition) the
parts are completed in order: after `](` the repository-relative paths of the
requirement and parameter files of the workspace, after `?` the `version=`
parameter, after `?version=` the current version of the linked requirement (or
the versions of the linked parameter, latest first), and after `#` the
requirement IDs or parameter names in the target file, the linked one first.
The link text (`REQ-1` or `@name`), or the anchor after the cursor, tells which
requirement or parameter is meant. Unsaved documents are offered and used.
Typing `[@` offers the parameters of the workspace and typing `[` followed by a
capital letter (`[REQ`) the requirement IDs. Choosing one replaces what was
typed, including a closing `]` added by an auto-pairing plugin, with the
complete link to the latest version, for example
`[@max_speed](/examples/vehicle_params.yaml?version=3#max_speed)`. The path and
version are shown next to each entry, which tells apart an ID defined in more
than one file. Nothing is offered when the cursor is inside an existing link.
Nothing else is offered outside the metadata line. The server asks the editor to
trigger completion after `:`, a space, `(`, `/`, `?`, `#`, `=`, `@` and `[`. Completion plugins such as
blink.cmp or nvim-cmp use it automatically; Neovim's built-in completion needs
`vim.lsp.completion.enable(true, client_id, bufnr, { autotrigger = true })`,
for example in an `LspAttach` autocommand.

In parameter files (see below) the field names are completed under a parameter
name: `value`, `unit`, `description` and `type` (only needed for tables), or
`description`, `columns` and `rows` once `type: table` is present, and `name` and
`unit` in a column item. Fields already present are left out. After `type:` the
only value is `table`. After `unit:` the units already used in the parameter files
of the workspace are offered first, then a short list of common units; values
that YAML would read as something else, such as `1` or `%`, are always inserted
quoted. Other units follow the style of the file: quoted if most `unit:` values in
the file are quoted, plain if most are plain; on a tie the style of the
workspace's parameter files decides, and without any example they are quoted. A
quote you have already typed is kept, and an auto-paired closing quote is
replaced together with it.
Parameter names and `value` are free text and are not completed.

## Find references

On a requirement heading ID, a `name_vN` key in a parameter file, or a link,
find references lists every link in the workspace that points at that
requirement or parameter, including `Parent:` links. Links to exactly the
version at the cursor come first. With `includeDeclaration` the heading or key
itself is listed first. Open, unsaved documents are searched with their current
content. In Neovim use `vim.lsp.buf.references()`.

## Document symbols

The outline of a requirement file lists each requirement ID with its metadata
as detail. In a parameter YAML file it lists each `name_vN` key. In Neovim use
`vim.lsp.buf.document_symbol()`. Parameter files are only outlined if the editor
sends them to the server (`"yaml"` in `filetypes`).

## Parameter files

Parameter YAML files are validated with the same rules as the build, and each
error is shown where it occurs. A `.yaml` file is treated as a parameter file if
it has a top-level key ending in `_v<digits>` (such as `max_speed_v1:`), so CI or
Docker YAML files are ignored. A wrongly written key like `maxSpeed_v1` still
counts, but a file whose only key lost its `_vN` suffix no longer does. The editor
must send YAML files to the server, so add `"yaml"` to `filetypes`.

Like the build, the whole-file rules (key names, version gaps, more than two
versions, colliding identifiers) are only checked once every parameter itself is
valid, so they can appear after earlier errors are fixed.

## Workspace symbols

Search requirement IDs and parameter keys (`name_vN`) across the whole
workspace by name. Matching is case-insensitive; prefix matches rank first, then
substring matches, then in-order character matches, and at most 200 results are
returned. Hidden directories, `bazel-*` output directories and `node_modules`
are skipped. Open, unsaved documents are searched with their current content.
In Neovim use `vim.lsp.buf.workspace_symbol("query")`.

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
| `FIRE016` | Reference-style link uses a label that is not defined    |
| `FIRE017` | Parameter file is not valid YAML                         |
| `FIRE018` | Parameter file violates a parameter rule                 |

Links are resolved against the nearest ancestor directory that contains a
`MODULE.bazel` or `WORKSPACE` file; without one only the syntax checks run.
Open documents are re-checked whenever another open document changes, using
its unsaved content, and when a Markdown or YAML file changes on disk (the
client must support dynamic file watching, which Neovim does).
`FIRE014` is an error for parameters and a warning for requirements, matching
the build. `FIRE015` is always a warning.
