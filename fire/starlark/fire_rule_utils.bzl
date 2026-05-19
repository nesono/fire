"""Shared helpers for FIRE Bazel rule implementations.

These utilities consolidate the boilerplate around invoking a Python
``py_binary`` from a custom rule: collecting its runfiles, assembling
the inputs list, and forwarding execution requirements.
"""

def run_python_script(
        ctx,
        *,
        script,
        script_target,
        args,
        extra_inputs,
        outputs,
        mnemonic,
        progress_message,
        use_default_shell_env = False,
        no_sandbox = False):
    """Run a Python ``py_binary`` as a Bazel action.

    Args:
        ctx: The rule context.
        script: ``File`` for the executable script (typically
            ``ctx.executable._script``).
        script_target: The script's ``Target`` (typically ``ctx.attr._script``),
            used to collect runfiles.
        args: ``Args`` object (or a plain list) with the script's CLI arguments.
        extra_inputs: List of additional input ``File`` objects (sources,
            dependencies, optional config). The script itself and its runfiles
            are added automatically.
        outputs: List of output ``File`` objects.
        mnemonic: Bazel mnemonic for the action.
        progress_message: Progress message printed during the build.
        use_default_shell_env: If True, run the action with the host shell
            environment. Only set this when the script genuinely needs it.
        no_sandbox: If True, request ``no-sandbox`` execution. Only set this
            when the script needs to read files outside the Bazel sandbox
            (e.g. when running outside the execroot).
    """
    runfiles = script_target[DefaultInfo].default_runfiles.files.to_list()
    inputs = list(extra_inputs) + [script] + runfiles

    arguments = args if type(args) == "list" else [args]

    execution_requirements = {}
    if no_sandbox:
        execution_requirements["no-sandbox"] = "1"

    ctx.actions.run(
        inputs = inputs,
        outputs = outputs,
        executable = script,
        arguments = arguments,
        mnemonic = mnemonic,
        progress_message = progress_message,
        use_default_shell_env = use_default_shell_env,
        execution_requirements = execution_requirements,
    )
