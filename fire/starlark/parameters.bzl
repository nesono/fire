"""Bazel rules for parameter management.

Parameters can be defined inline in BUILD files or loaded from separate .bzl files.
Validation happens at load time, and code is generated at build time for multiple languages.
"""

load("@rules_cc//cc:defs.bzl", "cc_library")
load("//fire/starlark:cpp_generator.bzl", "cpp_generator")
load("//fire/starlark:go_generator.bzl", "go_generator")
load("//fire/starlark:java_generator.bzl", "java_generator")
load("//fire/starlark:python_generator.bzl", "python_generator")
load("//fire/starlark:validator.bzl", "validator")

def _derive_namespace_from_package():
    """Derive namespace from Bazel package path.

    Converts package path to namespace format:
    - "vehicle/dynamics" -> "vehicle.dynamics"
    - "" (root) -> "root"
    - "foo/bar/baz" -> "foo.bar.baz"

    Returns:
        Namespace string with dots
    """
    pkg = native.package_name()
    if not pkg:
        return "root"
    return pkg.replace("/", ".")

def _get_python_namespace(namespace):
    """Convert namespace to Python format.

    Args:
        namespace: Dot-separated namespace

    Returns:
        Python module format (same as input)
    """
    return namespace

def _get_java_namespace(namespace, package_prefix = None):
    """Convert namespace to Java format.

    Args:
        namespace: Dot-separated namespace (e.g., "vehicle.dynamics")
        package_prefix: Optional prefix (e.g., "com.example")

    Returns:
        Java package format (e.g., "com.example.vehicle.dynamics")
    """
    if package_prefix:
        return package_prefix + "." + namespace
    return namespace

def _get_go_package_name(namespace):
    """Convert namespace to Go package name.

    Args:
        namespace: Dot-separated namespace (e.g., "vehicle.dynamics")

    Returns:
        Go package name (last component, e.g., "dynamics")
    """
    components = namespace.split(".")
    return components[-1]

def _get_source_label(name):
    """Get the source Bazel label for traceability.

    Args:
        name: Target name

    Returns:
        Bazel label string (e.g., "//vehicle/dynamics:vehicle_params")
    """
    pkg = native.package_name()
    if pkg:
        return "//{pkg}:{name}".format(pkg = pkg, name = name)
    return "//:{name}".format(name = name)

def parameter_library(
        name,
        schema_version = "1.0",
        namespace = None,
        parameters = []):
    """Define a parameter library inline in Starlark.

    Args:
        name: Name of the library
        schema_version: Schema version (default "1.0")
        namespace: C++ namespace for parameters (optional, derived from package path if not provided)
        parameters: List of parameter dictionaries

    Example:
        # Namespace auto-derived from package path
        parameter_library(
            name = "my_params",
            parameters = [
                {
                    "name": "max_velocity",
                    "type": "float",
                    "unit": "m/s",
                    "value": 55.0,
                    "description": "Maximum velocity",
                },
            ],
        )

        # Or explicitly specify namespace
        parameter_library(
            name = "my_params",
            namespace = "my.namespace",
            parameters = [...],
        )
    """

    # Derive namespace from package path if not provided
    if not namespace:
        namespace = _derive_namespace_from_package()

    # Get source label for traceability
    source_label = _get_source_label(name)

    param_data = {
        "namespace": namespace,
        "parameters": parameters,
        "schema_version": schema_version,
        "source_label": source_label,
    }

    # Validate at load time
    validation_error = validator.validate(param_data)
    if validation_error:
        fail("Parameter validation failed for {}: {}".format(name, validation_error))

    # Generate C++ header
    cpp_code = cpp_generator.generate(param_data)

    # Create a generated header file
    native.genrule(
        name = name,
        outs = [name + ".h"],
        cmd = """cat > $@ <<'EOF'
{}
EOF""".format(cpp_code),
        visibility = ["//visibility:public"],
    )

def cc_parameter_library(name, parameter_library, **kwargs):
    """Create a cc_library from a parameter_library.

    Args:
        name: Name of the cc_library
        parameter_library: Label of the parameter_library (the generated .h file)
        **kwargs: Additional arguments for cc_library
    """
    cc_library(
        name = name,
        hdrs = [parameter_library],
        includes = ["."],
        **kwargs
    )

def python_parameter_library(
        name,
        parameters,
        namespace = None,
        schema_version = "1.0"):
    """Generate Python module with parameters.

    Args:
        name: Name of the generated module (will create name.py)
        parameters: List of parameter dictionaries
        namespace: Python module namespace (optional, derived from package path if not provided)
        schema_version: Schema version (default "1.0")

    Example:
        # Namespace auto-derived from package path
        python_parameter_library(
            name = "vehicle_params",
            parameters = VEHICLE_PARAMS,
        )

        # Or explicitly specify namespace
        python_parameter_library(
            name = "vehicle_params",
            namespace = "vehicle.dynamics",
            parameters = VEHICLE_PARAMS,
        )
    """

    # Derive namespace from package path if not provided
    if not namespace:
        namespace = _derive_namespace_from_package()

    # Get source label for traceability
    source_label = _get_source_label(name)

    param_data = {
        "namespace": namespace,
        "parameters": parameters,
        "schema_version": schema_version,
        "source_label": source_label,
    }

    # Validate at load time
    validation_error = validator.validate(param_data)
    if validation_error:
        fail("Parameter validation failed for {}: {}".format(name, validation_error))

    # Generate Python code
    python_namespace = _get_python_namespace(namespace)
    python_code = python_generator.generate(python_namespace, parameters, source_label)

    # Create a generated Python file
    native.genrule(
        name = name,
        outs = [name + ".py"],
        cmd = """cat > $@ <<'EOF'
{}
EOF""".format(python_code),
        visibility = ["//visibility:public"],
    )

def java_parameter_library(
        name,
        parameters,
        namespace = None,
        package_prefix = None,
        class_name = "Parameters",
        schema_version = "1.0"):
    """Generate Java class with parameters.

    Args:
        name: Name of the generated class file
        parameters: List of parameter dictionaries
        namespace: Java package namespace (optional, derived from package path if not provided)
        package_prefix: Optional package prefix (e.g., "com.example")
        class_name: Name of the generated class (default "Parameters")
        schema_version: Schema version (default "1.0")

    Example:
        # Namespace auto-derived from package path
        java_parameter_library(
            name = "VehicleParams",
            class_name = "VehicleParams",
            package_prefix = "com.example",  # Optional
            parameters = VEHICLE_PARAMS,
        )

        # Or explicitly specify namespace
        java_parameter_library(
            name = "VehicleParams",
            namespace = "com.example.vehicle.dynamics",
            class_name = "VehicleParams",
            parameters = VEHICLE_PARAMS,
        )
    """

    # Derive namespace from package path if not provided
    if not namespace:
        base_namespace = _derive_namespace_from_package()
        namespace = _get_java_namespace(base_namespace, package_prefix)

    # Get source label for traceability
    source_label = _get_source_label(name)

    param_data = {
        "namespace": namespace,
        "parameters": parameters,
        "schema_version": schema_version,
        "source_label": source_label,
    }

    # Validate at load time
    validation_error = validator.validate(param_data)
    if validation_error:
        fail("Parameter validation failed for {}: {}".format(name, validation_error))

    # Generate Java code
    java_code = java_generator.generate(namespace, parameters, class_name, source_label)

    # Create a generated Java file
    native.genrule(
        name = name,
        outs = [class_name + ".java"],
        cmd = """cat > $@ <<'EOF'
{}
EOF""".format(java_code),
        visibility = ["//visibility:public"],
    )

def go_parameter_library(
        name,
        parameters,
        namespace = None,
        package_name = None,
        schema_version = "1.0"):
    """Generate Go package with parameters.

    Args:
        name: Name of the generated Go file (will create name.go)
        parameters: List of parameter dictionaries
        namespace: Go package namespace (optional, derived from package path if not provided)
        package_name: Go package name (optional, derived from last component of namespace if not provided)
        schema_version: Schema version (default "1.0")

    Example:
        # Namespace and package name auto-derived from package path
        go_parameter_library(
            name = "vehicle_params",
            parameters = VEHICLE_PARAMS,
        )

        # Or explicitly specify package name
        go_parameter_library(
            name = "vehicle_params",
            package_name = "dynamics",
            parameters = VEHICLE_PARAMS,
        )
    """

    # Derive namespace from package path if not provided
    if not namespace:
        namespace = _derive_namespace_from_package()

    # Derive package name from namespace if not provided
    if not package_name:
        package_name = _get_go_package_name(namespace)

    # Get source label for traceability
    source_label = _get_source_label(name)

    param_data = {
        "namespace": namespace,
        "parameters": parameters,
        "schema_version": schema_version,
        "source_label": source_label,
    }

    # Validate at load time
    validation_error = validator.validate(param_data)
    if validation_error:
        fail("Parameter validation failed for {}: {}".format(name, validation_error))

    # Generate Go code
    go_code = go_generator.generate(namespace, parameters, package_name, source_label)

    # Create a generated Go file
    native.genrule(
        name = name,
        outs = [name + ".go"],
        cmd = """cat > $@ <<'EOF'
{}
EOF""".format(go_code),
        visibility = ["//visibility:public"],
    )
