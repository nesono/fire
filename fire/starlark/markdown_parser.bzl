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
        Tuple of (type, data) where:
        - type is "parameter", "requirement", "test", "external", or "unknown"
        - data is (text, url) for validation
    """

    # Parameter reference: [@param_name](path/file.bzl#param_name)
    if text.startswith("@"):
        return ("parameter", (text[1:], url))

    # Requirement reference: [REQ-ID](path/to/REQ-ID.md)
    if url.endswith(".md"):
        return ("requirement", (text, url))

    # Test reference: [test_name](//package:target)
    if url.startswith("//") and ":" in url:
        return ("test", (text, url))

    # External or unknown
    if url.startswith("http://") or url.startswith("https://"):
        return ("external", (text, url))

    return ("unknown", (text, url))

def parse_markdown_references(body):
    """Parse all markdown references from requirement body.

    Args:
        body: Markdown body content

    Returns:
        Dictionary with keys:
        - "parameters": List of (param_name, param_path) tuples
        - "requirements": List of (req_id, req_path) tuples
        - "tests": List of (test_name, test_label) tuples
        - "external": List of (text, url) tuples
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
            ref_type, ref_data = _classify_reference(text, url)

            if ref_type == "parameter":
                refs["parameters"].append(ref_data)
            elif ref_type == "requirement":
                refs["requirements"].append(ref_data)
            elif ref_type == "test":
                refs["tests"].append(ref_data)
            elif ref_type == "external":
                refs["external"].append(ref_data)

    return refs

def validate_markdown_references(body, frontmatter_refs):
    """Validate markdown references against frontmatter with bi-directional checks.

    Validates:
    1. Link text matches reference name (no typos)
    2. All body references are declared in frontmatter
    3. All frontmatter references are used in body

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
        return None

    # Validate link text matches reference names
    for param_name, param_path in body_refs.get("parameters", []):
        if "#" in param_path:
            anchor = param_path.split("#")[1]
            if param_name != anchor:
                return "parameter link text '{}' does not match anchor '{}' in {}".format(
                    param_name,
                    anchor,
                    param_path,
                )

    for req_id, req_path in body_refs.get("requirements", []):
        filename = req_path.split("/")[-1] if "/" in req_path else req_path
        expected = req_id + ".md"
        if filename != expected:
            return "requirement link text '{}' does not match filename '{}' (expected '{}')".format(
                req_id,
                filename,
                expected,
            )

    for test_name, test_label in body_refs.get("tests", []):
        if ":" in test_label:
            target = test_label.split(":")[1]
            if test_name != target:
                return "test link text '{}' does not match target '{}' in {}".format(
                    test_name,
                    target,
                    test_label,
                )

    # Build sets for bi-directional validation
    # Frontmatter sets
    fm_params = set(frontmatter_refs.get("parameters", []))

    fm_reqs = set()
    for req_ref in frontmatter_refs.get("requirements", []):
        if type(req_ref) == "dict" and "path" in req_ref:
            fm_reqs.add(req_ref["path"])

    fm_tests = set(frontmatter_refs.get("tests", []))

    # Body sets
    body_params = set([path for _, path in body_refs.get("parameters", [])])
    body_reqs = set([path for _, path in body_refs.get("requirements", [])])
    body_tests = set([label for _, label in body_refs.get("tests", [])])

    # Check body references are in frontmatter
    for param_path in body_params:
        if param_path not in fm_params:
            return "body references parameter '{}' not declared in frontmatter".format(param_path)

    for req_path in body_reqs:
        if req_path not in fm_reqs:
            return "body references requirement '{}' not declared in frontmatter".format(req_path)

    for test_label in body_tests:
        if test_label not in fm_tests:
            return "body references test '{}' not declared in frontmatter".format(test_label)

    # Check frontmatter references are used in body
    for param_path in fm_params:
        if param_path not in body_params:
            return "frontmatter declares parameter '{}' not used in body".format(param_path)

    for req_path in fm_reqs:
        if req_path not in body_reqs:
            return "frontmatter declares requirement '{}' not used in body".format(req_path)

    for test_label in fm_tests:
        if test_label not in body_tests:
            return "frontmatter declares test '{}' not used in body".format(test_label)

    return None

# Export functions
markdown_parser = struct(
    parse_references = parse_markdown_references,
    validate_references = validate_markdown_references,
)
