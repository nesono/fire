# Publishing a New Release

1. In CHANGELOG.md, rename `[Unreleased]` to the new version and its date, add a new empty `[Unreleased]` section above it, and update the comparison links at the bottom
2. Change the version field in MODULE.bazel, README.md, and integration_test/MODULE.bazel.template
3. Update the `compatibility_level` in MODULE.bazel, if required
4. Create a new GitHub release — the `release.yaml` workflow uploads the source tarball and then, in a dependent job, opens a PR on `nesono/bazel-central-registry` with the new version
5. Review and merge the BCR PR
