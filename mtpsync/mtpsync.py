from pathlib import Path
import hashlib
import tempfile
import os
import sys
import argparse
import time

import yaml
import xdg.BaseDirectory

from mtpsync.helpers import notify_this, run_command, run_in_parallel, log

# ---CONFIG---------------------------
CONFIG_FILE = "mtpsync.yaml"


class MTPSync(object):
    def __init__(self, config_file):
        self.config_file = config_file
        assert self.config_file.exists()
        # directories to sync
        self.subtrees = []
        # excluded directories
        self.excluded = []
        # output
        self.output_directory = Path()
        # mtp path
        self.mtp_target = Path()
        # tmp mount point
        self.mount_point = tempfile.TemporaryDirectory()
        self.is_mounted = False
        self._load_config()

        self.known_tracks = []
        self.tracks = []

    def _load_config(self):
        with self.config_file.open() as data:
            configuration = yaml.load(data)
            self.output_directory = Path(configuration["output_directory"])
            self.mtp_target = Path(configuration["mtp_target"])
            assert self.output_directory.exists()
            self.subtrees = [Path(el) for el in configuration["directories"]
                             if Path(el).exists() and Path(el).is_absolute()]
            self.excluded = [Path(el) for el in configuration.get("excluded", [])
                             if Path(el).exists() and Path(el).is_absolute()]

    def __str__(self):
        return "Output:\n\t%s\nTo Sync:\n\t%s" % (self.output_directory, "\n\t".join([str(el) for el in self.subtrees]))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            log("\nGot interrupted. Trying to clean up.", color="red")
            if self.is_mounted:
                self.umount()

    def _diff_tracks(self):
        source_hashes = [el.hash for el in self.tracks]
        destination_hashes = [el.stem for el in self.known_tracks]

        to_delete = [el for el in self.known_tracks
                     if el.stem not in source_hashes]
        to_convert = [el for el in self.tracks
                      if el.hash not in destination_hashes]

        return to_delete, to_convert

    def refresh_tracks(self):
        # list known tracks
        for f in self.output_directory.rglob("*.mp3"):
            self.known_tracks.append(f)

        # list + hash target flac
        for subtree in self.subtrees:
            for f in subtree.rglob("*.flac"):
                # check if not in excluded dir
                excluded = [1 for p in self.excluded if f in p.parents]
                if not excluded:
                    self.tracks.append(Track(f, self.output_directory))
        run_in_parallel(lambda x: x.calculate_hash(), self.tracks, "Calculating hashes: ")

        # diff
        to_delete, to_convert = self._diff_tracks()
        log("%s tracks selected for export." % len(self.tracks), color="green")
        log("%s unused files will be deleted, %s new tracks will be converted." % (len(to_delete), len(to_convert)),
            color='green')

        # remove obsolete
        log("Deleting obsolete files...", color="boldblue")
        run_in_parallel(lambda x: os.remove(str(x)), to_delete, "Deleting: ")

        # convert not existing
        log("Converting new files...", color="boldblue")
        run_in_parallel(lambda x: x.convert(), to_convert, "Converting: ")

    def sync_tracks(self):
        log("Syncing files...", color="boldblue")
        destination = Path(self.mount_point.name, self.mtp_target)
        success, cmd_log = run_command(["rsync", "-ruv", "--delete", "--progress",
                                        self.output_directory.as_posix(), destination.as_posix()])
        if not success:
            log(cmd_log, color="red")

    def mount(self):
        log("Mounting mtp device...", color="boldblue")
        success, cmd_log = run_command(["simple-mtpfs", self.mount_point.name])
        if not success:
            log(cmd_log, color="red")
            raise Exception("Could not mount!")
        else:
            self.is_mounted = True

    def umount(self):
        log("Unmounting mpt device...", color="boldblue")
        success, cmd_log = run_command(["fusermount", "-u", self.mount_point.name])
        if not success:
            log(cmd_log, color="red")
            raise Exception("Could not unmount!")
        else:
            self.is_mounted = False

    def apply_replaygain(self):
        log("Calculating replaygain...", color="boldblue")
        success, cmd_log = run_command(["collectiongain", self.output_directory.as_posix()])
        if not success:
            log(cmd_log, color="red")

    def update_export(self):
        self.refresh_tracks()
        self.apply_replaygain()
        notify_this("MPTSync", "Converting done.")

    def sync(self):
        self.update_export()
        try:
            self.mount()
            self.sync_tracks()
            self.umount()
        except Exception as err:
            log(err, color="red")
            log("Is your device plugged in and unlocked?", color="red")
        finally:
            notify_this("MPTSync", "Sync done.")


class Track(object):
    def __init__(self, path, output_directory):
        self.path = path
        self.hash = ""
        self.output_directory = output_directory

    @property
    def output_path(self):
        return  Path(self.output_directory, self.hash[:2], "%s.mp3" % self.hash)

    def calculate_hash(self):
        with self.path.open("rb") as data:
            self.hash = hashlib.sha1(data.read()).hexdigest()

    def convert(self):
        if not self.output_path.parent.exists():
            self.output_path.parent.mkdir(parents=True)
        success, cmd_log = run_command(["ffmpeg",
                                        "-i", str(self.path),
                                        "-codec:a", "libmp3lame", "-qscale:a", "0",
                                        str(self.output_path)])
        if not success:
            print(cmd_log)

    def __str__(self):
        return "%s -> %s" % (self.path, self.output_path)


def main():
    log("\n# # # M T P S Y N C # # #", color="boldwhite")

    parser = argparse.ArgumentParser(description='MTPSync.\nSelect FLAC files, convert to mp3, sync with MTP device.')

    group_config = parser.add_argument_group('Configuration',
                                             'Manage configuration files.')
    group_config.add_argument('--config',
                              dest='config',
                              action='store',
                              metavar="CONFIG_FILE",
                              nargs=1,
                              help='Use an alternative configuration file.')

    group_actions = parser.add_argument_group('Actions',
                                              'Do things.')
    group_actions.add_argument('-r',
                               '--refresh',
                               dest='refresh',
                               action='store_true',
                               default=False,
                               help='Refresh export library.')

    group_actions.add_argument('-s',
                               '--sync',
                               dest='sync',
                               action='store_true',
                               default=False,
                               help='Sync export library with unlocked MTP device.')

    args = parser.parse_args()

    if args.config and Path(args.config[0]).exists():
        configuration_file = args.config[0]
    else:
        config_path = xdg.BaseDirectory.save_config_path("MTPSync")
        configuration_file = Path(config_path, CONFIG_FILE)
        try:
            assert configuration_file.exists()
        except AssertionError:
            log("No configuration file found at %s" % configuration_file, color="red")
            sys.exit(-1)

    overall_start = time.time()

    with MTPSync(configuration_file) as s:
        log(str(s), color="yellow")
        if args.refresh:
            s.update_export()
        elif args.sync:
            s.sync()

    overall_time = time.time() - overall_start
    log("\nEverything was done in %.2fs." % overall_time, color="boldwhite")
    notify_this("MTPSync", "Everything was done in %.2fs." % overall_time)

if __name__ == "__main__":
    main()
