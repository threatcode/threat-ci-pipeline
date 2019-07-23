# Debian pipeline for Developers

Build and test on reproducible environments on every push.


## Table of contents
* [Introduction](#introduction)
* [What does this pipeline gives to my project?](#what-does-this-pipeline-gives-to-my-project)
* [Basic Use](#basic-use)
* [Advanced Use](#advanced-use)
* [Support](#support)


## Introduction

The Salca CI Team work aims to improve the Debian packaging lifecycle by providing [Continuous Integration](https://about.gitlab.com/product/continuous-integration/) fully compatible with Debian packaging.

Currently all the building and testing performed by Debian QA is run asynchronusly and takes a long time to give feedback because it is only accessable after pushing a release to the archive.

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

> :warning: **Note:** On Debian projects, you would normally want to put this file under the `debian/` folder. For example `debian/salsa-ci.yml`.

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
There are many ways to skip a certain job.
An easy and simple solution is using an undefined variable to limit the job execution using the [`only`](https://docs.gitlab.com/ce/ci/yaml/#onlyvariablesexceptvariables) keyword.

```yaml
---
include: 
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/salsa-ci.yml
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/pipeline-jobs.yml

piuparts:
  extends: .test-piuparts
  only:
    variables:
      - $UNDEFINED_VAR_DISABLES_THIS
```

> :warning: **Note:** The job name **must** match with the one on [`pipeline-jobs.yml`](https://salsa.debian.org/salsa-ci-team/pipeline/blob/master/pipeline-jobs.yml).


### Only running selected jobs

If you want to use the definitions provided by the Salsa CI Team, but want to explicitly define which jobs to run, you might want to declare your YAML as follows:

```yaml
---
include: https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/salsa-ci.yml

variables:
  RELEASE: 'experimental'

build:
  extends: .build-package

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

### Running reprotest with diffoscope
Reprotest stage can be run with [diffoscope](https://try.diffoscope.org/), which is an useful tool that helps identifying reproducibility issues.
Large projects will not pass on low resources runners as the ones available right now. 

To enable diffoscope, extending the reprotest job from `test-reprotest-diffoscope` is needed.

```yaml
---
include: 
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/salsa-ci.yml
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/pipeline-jobs.yml

reprotest:
  extends: .test-reprotest-diffoscope
```

## Support
Write us on \#salsaci @ OFTC or open an [issue here](https://salsa.debian.org/salsa-ci-team/pipeline/issues) :)
