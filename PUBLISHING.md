# Publishing a New Release

1. Change the version field in MODULE.bazel
2. Create a new GitHub release
3. Download the source file
4. Upload again with `gh release upload v0.1.2 ~/Downloads/fire-0.1.2.tar.gz`
5. Go into `bazel-central-registry.git`
6. Run `bazel run //tools:add_module` and answer all questions
7. Run `bazel run //tools:update_integrity` if you changed archive contents
8. Test setup using `bazel run -- //tools:bcr_validation --check=fire@0.1.2`
9. Run pre-submit tests using `bazel run //tools:setup_presubmit_repos -- --module fire@0.1.2`
