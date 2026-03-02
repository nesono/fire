# Publishing a New Release

1. Change the version field in MODULE.bazel, README.md, and integration_test/MODULE.bazel.template
2. Update the `compatibility_level` in MODULE.bazel, if required
3. Create a new GitHub release and upload FORMAT_SPECIFICATION.md as a downloadable asset
4. Go into `bazel-central-registry.git`
5. Run `bazel run //tools:add_module` and answer all questions
6. Run `bazel run //tools:update_integrity` if you changed archive contents
7. Test setup using `bazel run -- //tools:bcr_validation --check=fire@0.2.1`
8. Run pre-submit tests using `bazel run //tools:setup_presubmit_repos -- --module fire@0.2.1`
