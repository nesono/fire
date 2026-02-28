# Publishing a New Release

1. Change the version field in MODULE.bazel, README.md, integration_test/MODULE.bazel.template, and FORMAT_SPECIFICATION.md
2. Create a new GitHub release and upload FORMAT_SPECIFICATION.md as a downloadable asset
3. Go into `bazel-central-registry.git`
4. Run `bazel run //tools:add_module` and answer all questions
5. Run `bazel run //tools:update_integrity` if you changed archive contents
6. Test setup using `bazel run -- //tools:bcr_validation --check=fire@0.2.1`
7. Run pre-submit tests using `bazel run //tools:setup_presubmit_repos -- --module fire@0.2.1`
