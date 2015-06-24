import subprocess
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count

from progressbar import Bar, Counter, ETA, Percentage, ProgressBar
import notify2

from mtpsync.logger import logger


def generate_progress_bar(title, number_of_elements):
    widgets = [title,
               Counter(),
               '/%s ' % number_of_elements,
               Percentage(),
               ' ',
               Bar(left='[', right=']', fill='-'),
               ' ',
               ETA()]
    return ProgressBar(widgets=widgets, maxval=number_of_elements).start()


def notify_this(title, text, icon="camera-photo"):
    notify2.init(title)
    n = notify2.Notification(title, text, icon)
    n.set_timeout(2000)
    n.show()


def run_in_parallel(function, source_list, title, num_workers=cpu_count() + 1):
    results = []
    if source_list:
        cpt = 0
        progress_bar = generate_progress_bar(title, len(source_list)).start()
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {executor.submit(function, el): el for el in source_list}
            for future in as_completed(futures):
                results.append(future.result())
                cpt += 1
                progress_bar.update(cpt)
        progress_bar.finish()
    return results


def run_command(command, project_root=None):
    start_dir = os.getcwd()
    if project_root:
        os.chdir(str(project_root))
    err_temp = tempfile.NamedTemporaryFile(delete=False)
    out_temp = tempfile.NamedTemporaryFile(delete=False)
    # print("DEBUG CMD", command)
    p = subprocess.Popen(command, stdout=out_temp, stderr=err_temp)
    p.wait()
    if project_root:
        os.chdir(start_dir)
    if p.returncode != 0:
        return False, " ERROR ==> \n%s\n%s" % (open(err_temp.name, 'r').read(), open(out_temp.name, 'r').read())
    else:
        return True, open(out_temp.name, 'r').read()


try:
    # colored input is optionnal
    from colorama import init
    init(autoreset=True)
    from colorama import Fore, Style

    colors = {
        "red": Fore.RED + Style.BRIGHT,
        "green": Fore.GREEN + Style.NORMAL,
        "boldgreen": Fore.GREEN + Style.BRIGHT,
        "blue": Fore.BLUE + Style.NORMAL,
        "boldblue": Fore.BLUE + Style.BRIGHT,
        "yellow": Fore.YELLOW + Style.NORMAL,
        "boldwhite": Fore.WHITE + Style.BRIGHT
    }

    def log(text, display=True, save=True, color=None):
        if display:
            if color in colors:
                print(colors[color] + text + Style.RESET_ALL)
            else:
                print(text)
        if save:
            logger.debug(text)
except ImportError:
    def log(text, display=True, save=True, color=None):
        if display:
            print(text)
        if save:
            logger.debug(text)
