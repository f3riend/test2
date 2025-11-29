from utils.observer import *
from utils.mail_manager import MailManager
from utils.tools import protect_file
from utils.unlock import Unlock
from utils.lock import Lock
from utils.logger import logger
import base64
import getpass
import click
import os


@click.group()
def secure_box():
    """Secure Box CLI"""
    pass


@secure_box.command()
@click.argument("folder")
@click.argument("filename")
@click.argument("password")
def lock(folder, filename, password):
    """Lock file into binary"""
    locker = Lock(password, folder, filename)
    locker.run()


@secure_box.command()
def config():
    print("Config")


@secure_box.command()
@click.argument("filename")
@click.argument("password")
def unlock(filename, password):
    """Unlock binary file"""
    unlocker = Unlock(password, filename)
    unlocker.run()


if __name__ == "__main__":
    secure_box()
