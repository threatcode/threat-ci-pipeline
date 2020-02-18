# Debian pipeline for Developers

Build and test on reproducible environments on every push.


## Table of contents
* [Introduction](#introduction)
* [What does this pipeline gives to my project?](#what-does-this-pipeline-gives-to-my-project)
* [Basic Use](#basic-use)
* [Advanced Use](#advanced-use)
* [Support](#support)


## Introduction

The Salsa CI Team work aims to improve the Debian packaging lifecycle by providing [Continuous Integration](https://about.gitlab.com/product/continuous-integration/) fully compatible with Debian packaging.

Currently all the building and testing performed by Debian QA is run asynchronusly and takes a long time to give feedback because it is only accessible after pushing a release to the archive.

Our [pipeline](https://docs.gitlab.com/ee/ci/pipelines.html) definition is focused on speeding up this process by giving developers faster feedback.


## What does this _pipeline_ provide for my project/package?

The [pipeline](https://docs.gitlab.com/ee/ci/pipelines.html) builds your package(s) and runs multiple checks on them after every push to Salsa.

This provides you with instant feedback about any problems the changes you made may have created or solved, without the need to do a push to the archive, speeding up your development cycle and improving the quality of packages uploaded to Debian.

While the pipeline is a Work-In-Progess project, it will always try to replicate the tests run by Debian QA.
The services we got working are the following:

 * Building the package from the source (only gbp is supported)
 * [Lintian](https://github.com/Debian/lintian)
 * Reproducible build using [Reprotest](https://reproducible-builds.org/tools)
 * [Piuparts](https://piuparts.debian.org)
 * [Autopkgtest](https://salsa.debian.org/ci-team/autopkgtest/raw/master/doc/README.package-tests.rst)
 * [Buildd Log Scanner](https://qa.debian.org/bls/)

Those services are enabled by something we called `salsa-pipeline` and it will be shared for all Salsa projects who adopt it.
Having this on Gitlab CI ensures that every package accomplishes the minimum quality to be in the archive and if we improve or add a new service the project will get the benefit instantaneously.


## Basic Use

To use the Salsa Pipeline, the first thing to do is to change the project's setting to make it point to the config file we are going to create later.
This can be done on `Settings` -> `CI/CD` (on the expanded menu, don't click on the CI / CD rocket) -> `General Pipelines` -> `Custom CI config path`.

> :warning: **Note:** On Debian projects, you would normally want to put this file under the `debian/` folder.

The recommended filename is `debian/salsa-ci.yml`.

The second step is to create and commit the file on the path set before with the following content:

```yaml
---
include:
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/salsa-ci.yml
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/pipeline-jobs.yml
```


## Advanced Use

Following the basic instructions will allow you to add all the building and testing stages as provided by the salsa-ci-team.
However, customization of the scripts is possible.


The [`salsa-ci.yml`](https://salsa.debian.org/salsa-ci-team/pipeline/blob/master/salsa-ci.yml) template delivers the jobs definitions.
Including only this file, no job will be added to the pipeline.
On the other hand, [`pipeline-jobs.yml`](https://salsa.debian.org/salsa-ci-team/pipeline/blob/master/pipeline-jobs.yml) includes all the jobs' instances.


### Changing the Debian Release

By default, everything will run on the `'unstable'` suite.
Changing the release is as easy as setting a `RELEASE` variable.

```yaml
---
include:
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/salsa-ci.yml
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/pipeline-jobs.yml

variables:
  RELEASE: 'buster'
```

The following releases are currently supported:
* jessie
* stretch
* stretch-backports
* buster
* buster-backports
* bullseye
* stable
* testing
* unstable
* experimental


### Building with non-free dependencies
By default, only `main` repositories are used.
If your package has dependencies or build-dependencies in the `contrib` or `non-free` components (archive areas), set `SALSA_CI_COMPONENTS` to indicate this:

```yaml
---
include:
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/salsa-ci.yml
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/pipeline-jobs.yml

variables:
    RELEASE: 'stretch'
    SALSA_CI_COMPONENTS: 'main contrib non-free'
```

This is currently used for `piuparts`, but is likely to be used for
other stages in future.


### Skipping a job
There are many ways to skip a certain job. The recommended way is to set to 1 (or "yes" or "true") the `SALSA_CI_DISABLE_*` variables that have been created for this purpose.

```yaml
---
include:
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/salsa-ci.yml
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/pipeline-jobs.yml

# This sample disables all default tests, only disable those that you
# don't want
variables:
  SALSA_CI_DISABLE_APTLY: 1
  SALSA_CI_DISABLE_AUTOPKGTEST: 1
  SALSA_CI_DISABLE_BLHC: 1
  SALSA_CI_DISABLE_LINTIAN: 1
  SALSA_CI_DISABLE_PIUPARTS: 1
  SALSA_CI_DISABLE_REPROTEST: 1
  SALSA_CI_DISABLE_BUILD_PACKAGE_ALL: 1
  SALSA_CI_DISABLE_BUILD_PACKAGE_ANY: 1
```


### Allow reprotest to fail
Reproducible builds are important, but `reprotest`'s behavior can sometimes be a little heractic and fail randomly on packages that aren't totally reproducible (yet!).

Without completely disabling `reprotest`, you can allow it to fail without failing the whole pipeline. That way, if `reprotest` fails, the pipeline will pass and show an orange warning telling you something went wrong.

You can allow `reprotest` to fail by adding this variable in your salsa-ci.yml manifest:

```
include:
 - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/salsa-ci.yml
 - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/pipeline-jobs.yml

reprotest:
  allow_failure: true
```


### Enabling the pipeline for tags
By default, the pipeline is run only for commits, tags are ignored. To run the pipeline against tags as well, export the `SALSA_CI_ENABLE_PIPELINE_ON_TAGS` variable and set it to one of "1", "yes" or "true", like in the following example:

```yaml
---
include:
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/salsa-ci.yml
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/pipeline-jobs.yml

variables:
  SALSA_CI_ENABLE_PIPELINE_ON_TAGS: 1
```


### Skipping the whole pipeline on push

There may be reasons to skip the whole pipeline for a `git push`, for example when you are adding `salsa-ci.yml` to hundreds of repositories or doing other mass-changes.

You can achieve this in two ways:

You can insert `[ci skip]` or `[skip ci]`, using any capitalization, in the commit message. With this marker, GitLab will not run the pipeline when the commit is pushed.

Alternatively, one can pass the `ci.skip` [Git push](https://git-scm.com/docs/git-push#Documentation/git-push.txt--oltoptiongt) option if using Git 2.10 or newer:

```
git push --push-option=ci.skip    # using git 2.10+
git push -o ci.skip               # using git 2.18+
```

See also https://docs.gitlab.com/ee/ci/yaml/#skipping-jobs

### Adding your private repositories to the builds

The variables `EXTRA_REPOSITORY` and `EXTRA_REPOSITORY_KEY` can be
used to add private apt repositories to the sources.list, to be
used by the build and tests, and (optionally) the signing key for the
repositories in armor format. These variables are of
[type file](https://docs.gitlab.com/ce/ci/variables/#variable-types),
which ease the multiline handling, but have the disadvantage that they can't
be set on the salsa-ci.yml file.

### Setting variables on pipeline creation

You can set these and other similar variables when launching a new pipeline in different ways:
 * Using the web interface under CI/CD, Run Pipeline, and setting the
desired variables.
 * Using the [gitlab API](https://docs.gitlab.com/ce/api/). For example,  check the script
[salsa_drive_build.py](https://salsa.debian.org/maxy/qt-kde-ci/blob/tooling/salsa_drive_build.py),
in particular the function
[launch_pipelines](https://salsa.debian.org/maxy/qt-kde-ci/blob/tooling/salsa_drive_build.py#L538).
 * Setting them as part of a pipeline triggered build.

### Only running selected jobs

If you want to use the definitions provided by the Salsa CI Team, but want to explicitly define which jobs to run, you might want to declare your YAML as follows:

```yaml
---
include: https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/salsa-ci.yml

variables:
  RELEASE: 'experimental'

build:
  extends: .build-package

test-build-any:
  extends: .test-build-package-any

test-build-all:
  extends: .test-build-package-all

reprotest:
  extends: .test-reprotest

lintian:
  extends: .test-lintian

autopkgtest:
  extends: .test-autopkgtest

blhc:
  extends: .test-blhc

piuparts:
  extends: .test-piuparts

aptly:
  extends: .publish-aptly
```

On the previous example, the package is built on Debian experimental and checked through on all tests currently provided.
You can choose to run only some of the jobs by deleting any of the definitions above.

As new changes are expected to happen from time to time, we **firmly recommend NOT to do define all jobs manually**.
Please consider if [skipping jobs](#skipping-a-job) meets your needs instead.

### Testing build of arch=any and arch=all packages

If your package contains binary packages for `all` or `any`, you may want to test if those can be build in isolation from the full build normally done.

This verifies the Debian buildds can build your package correctly when building for other architectures that the one you uploaded in or in case a binNMU is needed or you want to do source-only uploads.

The default `pipeline-jobs.yml` does this automatically based on the contents of `debian/control`, but if you manually define the jobs to run, you also need to include the `test-build-any` and `test-build-all` jobs manually as well:

```yaml
test-build-any:
  extends: .test-build-package-any

test-build-all:
  extends: .test-build-package-all
```

`.test-build-package-any` runs `dpkg-buildpackage` with the option `--build=any` and will only build arch-specific packages.

`.test-build-package-all` does the opposite and runs `dpkg-buildpackage` with the option `--build=all` building only arch-indep packages.

Note: These additional build jobs don't work with `RELEASE: 'jessie'` and are skipped in that case.

### Customizing reprotest

#### Running reprotest with diffoscope

Reprotest stage can be run with [diffoscope](https://try.diffoscope.org/), which is an useful tool that helps identifying reproducibility issues.
Large projects will not pass on low resources runners as the ones available right now.

To enable diffoscope, setting `SALSA_CI_REPROTEST_ENABLE_DIFFOSCOPE` to 1 (or 'yes' or 'true') is needed.

```yaml
---
include:
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/salsa-ci.yml
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/pipeline-jobs.yml

variables:
  SALSA_CI_REPROTEST_ENABLE_DIFFOSCOPE: 1
```

#### Adding extra arguments to reprotest

Sometimes it is desirable to disable some reprotest validations because the reproducibility issue comes inherently from the programming language being used, and not from the code being packaged. For example, some compilers embed the build path in the generated binaries.

You can get this level of customization by adding extra `reprotest` parameters in the `SALSA_CI_REPROTEST_ARGS` variable.

```yaml
---
include:
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/salsa-ci.yml
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/pipeline-jobs.yml

variables:
  SALSA_CI_REPROTEST_ARGS: --variations=-build_path
```

#### Adding extra arguments to dpkg-buildpackage

Sometimes it is desirable to add direct options to the dpkg-buildpackage that is run for the package building.

You can do this using the `SALSA_CI_DPKG_BUILDPACKAGE_ARGS` variable.

```yaml
---
include:
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/salsa-ci.yml
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/pipeline-jobs.yml

variables:
  SALSA_CI_DPKG_BUILDPACKAGE_ARGS: --your-option
```

#### Breaking up the reprotest job into the different variations

By default, reprotest applies all the known variations (`--variations=+all`,
see the full list at
[reprotest(1)](https://manpages.debian.org/buster/reprotest/reprotest.1.en.html)).
One way to debug a failing reprotest job and find out what variations are
producing unreproducibility issues is to run the variations independently.

If you want to run multiple reprotest jobs, one for each variation, set the
`SALSA_CI_ENABLE_ATOMIC_REPROTEST` variable to 1, 'yes' or 'true':

```yaml
---
include:
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/salsa-ci.yml
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/pipeline-jobs.yml

variables:
  SALSA_CI_ENABLE_ATOMIC_REPROTEST: 1
```

You can also set the `SALSA_CI_ENABLE_ATOMIC_REPROTEST` variable when
triggering the pipeline, without the need of creating a specific commit.


### Using automatically built apt repository
The [Aptly](https://www.aptly.info/) task runs in the publish stage and will save published apt repository files as its artifacts, so downstream CI tasks may access built binary/source packages directly through artifacts url via apt.

To find the url manually, click `Browse` (in the `Job artifacts` pane) -> `aptly` -> `index.html`. In brief it takes:

```bash
$ export BASE_URL=${CI_PROJECT_URL}/-/jobs/${CI_JOB_ID}/artifacts/raw/${REPO_PATH}
$ sudo wget ${BASE_URL}/public-key.asc | sudo apt-key add -
$ echo | sudo tee /etc/apt/sources.list.d/job-${CI_JOB_ID}.list <<EOF
deb ${BASE_URL} ${RELEASE} main
# deb-src ${BASE_URL} ${RELEASE} main
EOF
$ sudo apt-get update
```

This is currently disabled by default. Set `SALSA_CI_DISABLE_APTLY` to anything other than 1, 'yes' or 'true' to enable it.

To specify repository signing key, export the gpg key/passphrase as CI / CD [Variables](https://salsa.debian.org/help/ci/variables/README#variables) `SALSA_CI_APTLY_GPG_KEY` and `SALSA_CI_APTLY_GPG_PASSPHRASE`. Otherwise, an automatically generated one will be used.

### Debian release bump
By default, the build job will increase the release number using the +sci suffix.
To disable this behavior set the `SALSA_CI_DISABLE_VERSION_BUMP` to 1, 'yes' or 'true'.

## Hacking

### Allow images to be persistent

By default all images are deleted when the pipeline is finished. This is to avoid images
being created and stored in the registry when the project is forked.

To disable this behavior set the `SALSA_CI_PERSIST_IMAGES` to 1, 'yes' or
'true' on a CI variable (*CI/CD Settings*).

## Support
Write us on \#salsaci @ OFTC or open an [issue here](https://salsa.debian.org/salsa-ci-team/pipeline/issues) :)
