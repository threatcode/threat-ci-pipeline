# Debian pipeline for Developers

Gitlab integrates very well the continuous integration (CI) with the repository, so since Debian has migrated to Gitlab we can have CI in our repositories easily. Actually, we can have the same services that Debian QA offers today but before uploading a release to the archive. The main idea is having a faster feedback when you are working in a package, it is not intended to replace Debian QA. Debian QA services are the answer if you want to know if your package is reproducible or if piuparts is passing ok, etc.

We started looking for the services that Debian QA is offering today and tried to reach the same point but inside Gitlab CI. The services we got working until now, are the following:

 * Building the package from the source (only gbp is supported for now)
 * Lintian check
 * Reproducible build (Using reprotest)
 * piuparts
 * Autopkgtest
 * Buildd Log Scanner

Those services are enabled by something we called `salsa-pipeline` and it'll be shared for all Gitlab projects who adopt it. Having the same pipeline on GCI ensure that every package accomplishes the minimum quality to be in the archive and if we improve or add a new service the project will get the benefit instantaneously.


## Using Salsa-Pipeline

This project provides the definition of build and test jobs.
It you want to use this tools to build and test your project, adding the following definitions to your `gitlab-ci.yml` file is the only thing you need to do.

```yaml
include: https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/salsa-ci.yml

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

On Debian projects, you would normally want to put this file under the `debian/` folder, so changing the config path on your project will be necessary.
This can be done on `Settings` -> `CI/CD` -> `General Pipelines` -> `Custom CI config path`.

Due to current `include` limitations, yaml anchors can't be used here, so every job has to be defined and extended with the corresponding definition from the included file.

On the previous example, the package is built on Debian unstable and tested on all five tests.
You can choose to run only some of the jobs. 
Anyway, we **firmly recommend NOT to do it**.

### Including the job implementation

The `salsa-ci.yml` template only delivers the jobs definitions. Including only this file, no job will be added to the pipeline.
On the other hand, `pipeline-jobs.yml` includes all the jobs' _implementation_.

To use this, simply add a `debian/gitlab-ci.yml` like the following:

```yaml
include: 
 - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/salsa-ci.yml
 - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/pipeline-jobs.yml

variables:
 RELEASE: 'unstable'
```

`RELEASE: 'unstable'` can be replaced with any of the releases provided.

### Building
The Debian release can be specified declaring the variable `RELEASE` on any of the images availables.
 - unstable
 - stretch-backports
 - stretch
 - jessie

This release is also gonna be used for some stages like lintian.
By default, `unstable` is used.

To change the `RELEASE`, define this after including the yaml:
```yaml
variables:
    RELEASE: 'stretch'
```
Replace `stretch` with any of the releases listed previously.


### Testing
5 different tests are available to be used:
 - [test-autopkgtest](https://salsa.debian.org/ci-team/autopkgtest/raw/master/doc/README.package-tests.rst)
 - [test-lintian](https://github.com/Debian/lintian)
 - [test-reprotest](https://reproducible-builds.org/tools)
   - Reprotest stage can be run with diffoscope, which is an useful tool that helps identifying reproducibility issues. Large projects won't pass on low resources runners as the ones available right now. To use it, just extend from `test-reprotest-diffoscope`
 - [test-piuparts](https://piuparts.debian.org)
 - [test-blhc](https://qa.debian.org/bls/)
