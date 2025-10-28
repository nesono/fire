"""Markdown reference parsing and validation."""

def _parse_markdown_link(line):
    """Parse markdown links from a line.

    Args:
        line: Line of markdown text

    Returns:
        List of (text, url) tuples for links found in the line
    """
    links = []

    for i in range(len(line)):
        # Find opening [
        if line[i] != "[":
            continue

        # Find closing ]
        text_start = i + 1
        text_end = -1
        for j in range(text_start, len(line)):
            if line[j] == "]":
                text_end = j
                break

        if text_end == -1:
            continue

        # Check for (url)
        if text_end + 1 >= len(line) or line[text_end + 1] != "(":
            continue

        # Find closing )
        url_start = text_end + 2
        url_end = -1
        for k in range(url_start, len(line)):
            if line[k] == ")":
                url_end = k
                break

        if url_end == -1:
            continue

        # Extract link
        text = line[text_start:text_end]
        url = line[url_start:url_end]
        links.append((text, url))

    return links

def _classify_reference(text, url):
    """Classify a markdown reference by type.

    Args:
        text: Link text
        url: Link URL

    Returns:
        Tuple of (type, id) where type is one of:
        - "parameter": Parameter reference (starts with @)
        - "requirement": Requirement reference (.md file)
        - "test": Test reference (BUILD file)
        - "external": External link
        - "unknown": Unknown reference type
    """

    # Parameter reference: [@param_name](path)
    if text.startswith("@"):
        param_name = text[1:]  # Remove @ prefix
        return ("parameter", param_name)

    # Requirement reference: [REQ-ID](REQ-ID.md)
    if url.endswith(".md"):
        # Extract requirement ID from URL
        # Handle both "REQ-ID.md" and "path/to/REQ-ID.md"
        parts = url.split("/")
        filename = parts[-1]
        if filename.endswith(".md"):
            req_id = filename[:-3]  # Remove .md extension
            return ("requirement", req_id)

    # Test reference: [test](BUILD.bazel#target)
    if "BUILD.bazel" in url or "BUILD" in url:
        # Extract test name from anchor if present
        if "#" in url:
            parts = url.split("#")
            test_name = parts[-1]
            return ("test", test_name)
        return ("test", text)

    # External or unknown
    if url.startswith("http://") or url.startswith("https://"):
        return ("external", url)

    return ("unknown", url)

def parse_markdown_references(body):
    """Parse all markdown references from requirement body.

    Args:
        body: Markdown body content

    Returns:
        Dictionary with keys:
        - "parameters": List of parameter names
        - "requirements": List of requirement IDs
        - "tests": List of test names
        - "external": List of external URLs
    """
    refs = {
        "external": [],
        "parameters": [],
        "requirements": [],
        "tests": [],
    }

    if not body:
        return refs

    lines = body.split("\n")
    for line in lines:
        links = _parse_markdown_link(line)
        for text, url in links:
            ref_type, ref_id = _classify_reference(text, url)

            if ref_type == "parameter":
                refs["parameters"].append(ref_id)
            elif ref_type == "requirement":
                refs["requirements"].append(ref_id)
            elif ref_type == "test":
                refs["tests"].append(ref_id)
            elif ref_type == "external":
                refs["external"].append(ref_id)

    return refs

def validate_markdown_references(body, frontmatter_refs):
    """Validate markdown references against frontmatter.

    Checks that all markdown references in the body are also declared
    in the frontmatter references section.

    Args:
        body: Markdown body content
        frontmatter_refs: References from frontmatter (dict)

    Returns:
        None if valid, error message if invalid
    """
    if not body:
        return None

    body_refs = parse_markdown_references(body)

    # If no frontmatter references, but we have body references, that's an error
    if not frontmatter_refs:
        total_refs = (len(body_refs.get("parameters", [])) +
                      len(body_refs.get("requirements", [])) +
                      len(body_refs.get("tests", [])))
        if total_refs > 0:
            return "markdown body contains references but frontmatter has no references section"

    # Check parameters
    body_params = body_refs.get("parameters", [])
    fm_params = frontmatter_refs.get("parameters", []) if frontmatter_refs else []
    for param in body_params:
        if param not in fm_params:
            return "markdown references parameter '{}' not declared in frontmatter".format(param)

    # Check requirements
    body_reqs = body_refs.get("requirements", [])
    fm_reqs = frontmatter_refs.get("requirements", []) if frontmatter_refs else []
    for req in body_reqs:
        if req not in fm_reqs:
            return "markdown references requirement '{}' not declared in frontmatter".format(req)

    # Check tests
    body_tests = body_refs.get("tests", [])
    fm_tests = frontmatter_refs.get("tests", []) if frontmatter_refs else []
    for test in body_tests:
        # Test references can be target names or full labels
        # Match if the test name appears in any frontmatter test reference
        found = False
        for fm_test in fm_tests:
            if test in fm_test or fm_test.endswith(":" + test):
                found = True
                break
        if not found:
            return "markdown references test '{}' not declared in frontmatter".format(test)

    return None

# Export functions
markdown_parser = struct(
    parse_references = parse_markdown_references,
    validate_references = validate_markdown_references,
)
