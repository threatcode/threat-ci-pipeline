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

The `salsa-ci.yml` template only delivers the jobs definitions. Including only this file, no job will be added to the pipeline.
On the other hand, `pipeline-jobs.yml` includes all the jobs' implementations.

To use the Salsa Pipeline, you first have to change the project's setting to make it point to the config file we're going to create later.
This can be done on `Settings` -> `CI/CD` (on the expanded menu, don't click on the CI / CD rocket) -> `General Pipelines` -> `Custom CI config path`.
On Debian projects, you would normally want to put this file under the `debian/` folder. For example `debian/salsa-ci.yml`.

The second step is to create and commit the file on the path set before with the following content:

```yaml
include:
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/salsa-ci.yml
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/pipeline-jobs.yml
```

By default, everything will run against the `'unstable'` suite. Changing the suite is as easy as setting a `RELEASE`.

```yaml
include:
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/salsa-ci.yml
  - https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/pipeline-jobs.yml

variables:
  RELEASE: 'unstable'
```

### Including only the jobs' definition

The `salsa-ci.yml` file provides the definition of build and test jobs.
It you want to use this tools to build and test your project, but you want to explicitly define which jobs to run, you can do as follows:

```yaml
include: https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/salsa-ci.yml

variables:
  RELEASE: 'unstable'

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

On the previous example, the package is built on Debian unstable and tested on all five tests.
You can choose to run only some of the jobs.
Anyway, we **firmly recommend NOT to do it**.

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

### Building
The Debian release can be specified declaring the variable `RELEASE` on any of the images availables.
 - experimental
 - unstable
 - buster
 - stretch-backports
 - stretch
 - jessie

This release is also going to be used for some stages like lintian.
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
```yaml
include: https://salsa.debian.org/salsa-ci-team/pipeline/raw/master/salsa-ci.yml

reprotest:
  extends: .test-reprotest-diffoscope
````
 - [test-piuparts](https://piuparts.debian.org)
 - [test-blhc](https://qa.debian.org/bls/)

## Support
\#salsaci on OFTC or open an issue here.
