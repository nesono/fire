#!/usr/bin/env python3
"""Parse BUILD files to extract target names and tags using tree-sitter.

This script uses tree-sitter to parse BUILD.bazel files and extract
failure test targets with their associated tags. This is much faster
than using bazel query for each target.
"""

import sys
from pathlib import Path

try:
    from tree_sitter import Language, Parser
    import tree_sitter_python as tspython
except ImportError:
    print("ERROR: tree-sitter not installed. Install with:", file=sys.stderr)
    print("  pip install tree-sitter tree-sitter-python", file=sys.stderr)
    sys.exit(1)


def find_repo_root():
    """Find git repository root by looking for .git directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    print("ERROR: Could not find git repository root", file=sys.stderr)
    sys.exit(1)


def extract_string_value(node):
    """Extract string value from a string literal node."""
    if node.type == "string":
        # Remove quotes from string literal
        return node.text.decode("utf-8").strip('"').strip("'")
    return None


def extract_list_strings(node):
    """Extract all string values from a list node."""
    if node.type != "list":
        return []

    strings = []
    for child in node.children:
        if child.type == "string":
            value = extract_string_value(child)
            if value:
                strings.append(value)
    return strings


def extract_target_info(call_node):
    """Extract target name and tags from a function call node.

    Args:
        call_node: tree-sitter node representing a function call

    Returns:
        Tuple of (target_name, tags_list) or (None, None) if not found
    """
    if call_node.type != "call":
        return None, None

    name = None
    tags = []

    # Find the argument_list child
    arg_list = None
    for child in call_node.children:
        if child.type == "argument_list":
            arg_list = child
            break

    if not arg_list:
        return None, None

    # Parse keyword arguments
    for child in arg_list.children:
        if child.type == "keyword_argument":
            # Get the parameter name and value
            param_name = None
            param_value = None

            for subchild in child.children:
                if subchild.type == "identifier":
                    param_name = subchild.text.decode("utf-8")
                elif subchild.type in ("string", "list"):
                    param_value = subchild

            if param_name == "name" and param_value:
                name = extract_string_value(param_value)
            elif param_name == "tags" and param_value:
                tags = extract_list_strings(param_value)

    return name, tags


def parse_build_file(build_file, repo_root):
    """Parse a single BUILD file and extract failure test targets.

    Args:
        build_file: Path to BUILD.bazel file
        repo_root: Path to repository root

    Yields:
        Tuples of (target, tags_str) for each failure test target
    """
    PY_LANGUAGE = Language(tspython.language())
    parser = Parser(PY_LANGUAGE)

    with open(build_file, "rb") as f:
        tree = parser.parse(f.read())

    # Calculate package path (relative to repo root)
    rel_path = build_file.parent.relative_to(repo_root)
    package = f"//{rel_path}"

    # Walk the AST to find function calls
    def visit_node(node):
        if node.type == "expression_statement":
            # Check if this is a function call
            for child in node.children:
                if child.type == "call":
                    name, tags = extract_target_info(child)

                    # Skip _validation targets and targets without failure_test tag
                    if (
                        name
                        and not name.endswith("_validation")
                        and "failure_test" in tags
                    ):
                        target = f"{package}:{name}"
                        tags_str = " ".join(tags)
                        yield target, tags_str

        # Recursively visit children
        for child in node.children:
            yield from visit_node(child)

    # Visit all nodes in the tree
    yield from visit_node(tree.root_node)


def main():
    """Parse all BUILD files in failure_test directory."""
    repo_root = find_repo_root()
    failure_test_dir = repo_root / "fire" / "starlark" / "failure_test"

    if not failure_test_dir.exists():
        print(
            f"ERROR: Failure test directory not found: {failure_test_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Parse all BUILD.bazel files
    for build_file in failure_test_dir.rglob("BUILD.bazel"):
        for target, tags_str in parse_build_file(build_file, repo_root):
            print(f"{target}|{tags_str}")


if __name__ == "__main__":
    main()
