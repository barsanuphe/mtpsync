# MTPSync

## What it is

**MPTSync** is a script to:

- select directories containing FLAC files
- convert them to mp3 V0 in a separate output directory
- mount an MTP device and sync the mp3s on the device.

The mp3 files are named after the sha1 hash of the original FLAC files,
so that it is easy to check if a previously converted files must be
re-encoded or not.

This makes the assumption that the music player on the MTP device (say,
like any music player on an Android phone) will extract the tags from the
files and never show filenames.

Another assumption is that all files are correctly tagged. For this, use
the excellent [beets](beets.radbox.org).

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)

### Requirements

**MPTSync** runs on Linux (tested in Archlinux only).

Current requirements:
- python (3.4+)
- python-yaml
- python-notify2
- python-progressbar
- python-rgain
- simple-mtpfs

External binaries required:
- [ffmpeg](https://www.ffmpeg.org/) (which should install in turn the lame mp3 encoder)
- [collectiongain](https://github.com/bup/bup) (installed by python-rgain)
- [rsync](https://rsync.samba.org/)

### Installation

After cloning this repository, run:

    $ sudo python setup.py install

To uninstall (not sure why one would want to do such a thing), run:

    $ sudo pip uninstall mtpsync

The configuration file *mtpsync.yaml* is expected to be in
`$XDG_CONFIG_HOME/mtpsync/`. You might want to `ln -s` your actual configuration
file there, because let's face it, `$XDG_CONFIG_HOME` is a sad and lonely place
you never visit.

Logs are in `$XDG_DATA_HOME/mtpsync`.

### Usage


    TODO


### Configuration

**MTPSync** uses a yaml file to describe
- the `output_directory`: the directory where mp3s will be created.
- the `mtp_target`: the path on the MTP device where to sync the mp3 files.
- `directories`: list of directories in which FLAC files will recursively be selected.
- `excluded`: list of directories which will be excluded from the above.

Here is the general structure of how to describe a repository for **MTPSync**:

    output_directory: /home/user/out
    mtp_target: Card/music
    directories:
        - /home/user/music/classical
        - /home/user/music/death_metal
    excluded:
        -  /home/user/music/classical/wagner