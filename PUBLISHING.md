# Publishing a New Release

1. Change the version field in MODULE.bazel, README.md, and integration_test/MODULE.bazel.template
2. Update the `compatibility_level` in MODULE.bazel, if required
3. Create a new GitHub release — the `release.yaml` workflow uploads the source tarball and then, in a dependent job, opens a PR on `nesono/bazel-central-registry` with the new version
4. Review and merge the BCR PR
