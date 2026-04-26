# Publishing a New Release

1. Change the version field in MODULE.bazel, README.md, and integration_test/MODULE.bazel.template
2. Update the `compatibility_level` in MODULE.bazel, if required
3. Create a new GitHub release — the `release.yaml` workflow uploads the tarball and FORMAT_SPECIFICATION.md automatically
4. The `bcr-publish.yaml` workflow automatically creates a PR on `nesono/bazel-central-registry` with the new version
5. Review and merge the BCR PR
