To contribute, forking the project and opening a merge request should be straight forward.

Things to take into consideration:

1. The branch name is used as a staging tag on the generated images.
Because of this, slashes (`/`) are not allowed, otherwise CI will fail.
Avoid branch names like `something/other`.

1. Your fork should have 'Public' visibility for the pipeline to be shown on the merge request.

1. Please sign your commits. Debian relies on OpenPGP to guarantee the
authenticity and integrity of contributions.

1. YAML files follow a two-space indentation. Scripts in other languages should
follow their language-wide coding style.