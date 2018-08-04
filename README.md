Debian pipeline for Developers
==============================

Gitlab integrates very well the continuous integration (CI) with the repository, so since Debian has migrated to Gitlab we can have CI in our repositories easily. Actually, we can have the same services that Debian QA offers today but before uploading a release to the archive. The main idea is having a faster feedback when you are working in a package, it is not intended to replace Debian QA. Debian QA services are the answer if you want to know if your package is reproducible or if piuparts is passing ok, etc.

We started looking for the services that Debian QA is offering today and tried to reach the same point but inside Gitlab CI. The services we got working until now, are the following:

 * Building the package from the source (only gbp is supported for now)
 * Lintian check
 * Reproducible build (Using reprotest)
 * piuparts
 * Autopkgtest

Those services are enabled by something we called `salsa-pipeline` and it'll be shared for all Gitlab projects who adopt it. Having the same pipeline on GCI ensure that every package accomplishes the minimum quality to be in the archive and if we improve or add a new service the project will get the benefit instantaneously.


HowTo
=====

In order to add your project to the list of updated repositories, 3 steps are mandatory:

1. Add @salsa-pipeline-guest as `Developer` in the project. This is the minimum permission necessary to push branches and open Merge Requests.

2. Change the Gitlab CI YAML location from `.gitlab-ci.yml` to `debian/gitlab-ci.yml`. It can be changed in Settings -> CI/CD -> General Pipelines -> Custom CI config path.

3. Open a Merge Request on this project adding your repo to the `repositories.py` file.
