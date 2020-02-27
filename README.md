# fd.o CI templates

This repository contains a set of templates that are used by some of the
freedesktop.org projects.

Current projects using this are (non exhaustive list):
- https://gitlab.freedesktop.org/xorg/xserver
- https://gitlab.freedesktop.org/libinput/libinput
- https://gitlab.freedesktop.org/wayland/weston
- https://gitlab.freedesktop.org/mesa/mesa

History of the creation and various MR for these projects:
- https://gitlab.freedesktop.org/wayland/weston/merge_requests/98 (closed in favor of 117)
- https://gitlab.freedesktop.org/wayland/weston/merge_requests/117
- https://gitlab.freedesktop.org/xorg/xserver/merge_requests/149
- https://gitlab.freedesktop.org/libinput/libinput/merge_requests/181
- https://gitlab.freedesktop.org/mesa/mesa/merge_requests/543

# Why should I use these templates in my project?

## multiple tests uses case (see [mesa](https://gitlab.freedesktop.org/mesa/mesa/blob/master/.gitlab-ci.yml) for an example)
Let's say you have a project that runs a bunch of tests.
Ideally, you want to split the tests in separate jobs to visually know which
test fails without having to dive into the logs and understand which test fails.

*But* your project needs some dependencies to be able to compile and run the
tests, and those dependencies would need to be pulled for every test.
This adds a lot of overhead for each job, as you likely need to update the
packages in the image, install the dependencies and configure everything.

So you have the idea of creating a new base image for you. And this is exactly
what these templates are: they allow a project to create a new base test image.

## distribution testing (see [libinput](https://gitlab.freedesktop.org/libinput/libinput/blob/master/.gitlab-ci.yml) for an example)

You now want to make sure your project compiles on some major distributions.
That will give you a heads up when some dependency break your project, and can
avoid you some bug reports from users saying that it broke under *X*.

In this case, the recommended setup is to update the images in a scheduled
pipeline (once a week, once a month, it's up to you). You then recreate all of
your base testing images, and re-run your tests on them.

So if at some point one image fails, you can compare with the previous one, and
check which packages are different and ideally deduce what happened.

## OK, but why do I need to use a template when I can just rely on my own custom script?

These templates have several benefits from writing a custom script:
- they rely on `buildah`, `skopeo` and `podman` to create the image\
  This means that you do not need `docker-in-docker` to create the image.
  Using skopeo means less bandwidth used as you can copy a tag on a distant
  registry without having to pull and re-push the image.
- they are fancy: a fork can actually update the base image by changing its tag\
  When the image creation job is run, it checks for the current local registry
  to see if it has the given image. If not, it pulls the one from the upstream
  repo. And finally, if the image is not available, it will create it
- they take care of shrinking the image for you\
  When using a debian-like flavour, the man pages are not installed by default.
  Also, before storing the image and pushing it, the templates are cleaning
  the package manager used by the system.
- you do not need to use a `Dockerfile`\
  Writing a `Dockerfile` can be hard, and can give some headaches. By default,
  each `RUN` command will create a new snapshot of your image (a layer).
  This has several benefits, because you can have smaller incremental changes.
  But most of the time, people tend to forget to call `apt-get clean` or
  `dnf clean` and each of these layers would contain the package manager cache.
  It's not too bad, but that means that if you try to remove this cache in your
  final `RUN`, then this is pointless.
- you can use major Linux distributions without having to know each of them\
  Debian, Ubuntu, Fedora and Arch are supported, more are coming.

## But I still want to use `docker`, `kaniko`, ...

Well, you can, but this repo is making sure the creation of the image works.
There is even a CI script that checks if a new base image will be working on the
templates. So if you dislike `buildah`, you are free to not use this, but the
tools here are relying on the Open Container Initiative and are not tied to
a specific corporation.

# How can I use it?

A simple example (using debian) would be:

```yaml
variables:
  # DEBIAN_TAG can be anything, what matters is that it is unique enough and
  #            every change will rebuild a new image
  DEBIAN_TAG: 2019-03-29-01
  DISTRIBUTION_VERSION: testing
  TEST_IMAGE: "$CI_REGISTRY_IMAGE/debian/$DISTRIBUTION_VERSION:$DEBIAN_TAG"

# this is where the magic happens
# `ref` can be a git sha or a git ref (master)
include:
  - project: 'wayland/ci-templates'
    ref: c73dae8b84697ef18e2dbbf4fed7386d9652b0cd
    file: '/templates/debian.yml'

stages:
  - containers-build
  - test

# CONTAINERS creation stage
container_build:
  extends: .debian@container-ifnot-exists
  stage: containers-build
  variables:
    GIT_STRATEGY: none # no need to pull the whole tree for rebuilding the image
    # a list of packages to install
    DISTRIBUTION_PACKAGES: 'curl'

# TEST stage (is curl working?)
test_curl:
  image: $TEST_IMAGE
  stage: test
  script:
    - curl --insecure https://gitlab.freedesktop.org
```

For a more detailed documentation, have a look at the template you want to use.

# Qemu

Those templates are capable of generating a base container image that can run
`qemu` directly in a privileged container with `/dev/kvm` access.

Some helpers are available to start the produced VM in the container:
- once the image is built, you can start it with `/app/start_vm.sh`
- if you want to test a newly built kernel, you can use:
  `/app/start_vm_kernel.sh my-new-kernel`

(see https://gitlab.freedesktop.org/wayland/ci-templates/merge_requests/6 for an
explanation on how we can produce the VM images).

# Pain points when using templates

## registries are not pruned when you delete a tag

If you have 2 tags pointing at the same image, and you remove one of them, the
registry still keeps the blobs because there is still a tag attached to it.

*But* there are countless of reports[1, 2, 3, 4] that if you remove a tag or
even a blob from the registry, and that nothing still points at it, the blobs
data is not removed from the physical disk.

Gitlab provides a garbage collector [5] that can be run from the host hosting
the registry, but, and I quote:
> **As of today we are still afraid of executing that on production data.
> There's no warranty that it will not break repository.**

So it's a world where everything that is pushed to a registry is supposed to be
kept forever, because *something* might refer the blob sha in the future...
sigh.

[1] https://gitlab.com/gitlab-org/gitlab-ce/issues/25322 \
[2] https://serverfault.com/questions/905065/docker-private-registry-deleted-all-images-but-still-showing-in-catalog \
[3] https://github.com/docker/docker-registry/issues/988 \
[4] https://medium.com/@mcvidanagama/cleanup-your-docker-registry-ef0527673e3a \
[5] https://gitlab.com/gitlab-org/docker-distribution-pruner
