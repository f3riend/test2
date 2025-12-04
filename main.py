import click
from utils.lock import Lock
from utils.unlock import Unlock
from utils.logger import auto_logger


logger = auto_logger()


@click.group()
def cli():
    """Secure Box - File encryption tool"""
    pass


@cli.command()
@click.argument('folder', type=click.Path(exists=True))
@click.argument('output', type=str)
@click.argument('password', type=str)
@click.option('--resume', is_flag=True, help='Resume from checkpoint if available')
@click.option('--threads', default=4, help='Number of threads for encryption (default: 4)')
@click.option('--no-threading', is_flag=True, help='Disable multi-threading')
def lock(folder, output, password, resume, threads, no_threading):
    """Lock (encrypt) a folder"""
    try:
        locker = Lock(password, folder, output, max_workers=threads)
        locker.run(resume=resume, use_threading=not no_threading)
        click.echo(click.style("✓ Folder locked successfully!", fg='green'))
    except Exception as e:
        logger.error(f"Lock failed: {e}")
        click.echo(click.style(f"✗ Lock failed: {e}", fg='red'))
        raise SystemExit(1)


@cli.command()
@click.argument('data_file', type=str)
@click.argument('password', type=str)
def unlock(data_file, password):
    """Unlock (decrypt) a folder"""
    try:
        unlocker = Unlock(password, data_file)
        unlocker.run()
        click.echo(click.style("✓ Folder unlocked successfully!", fg='green'))
    except Exception as e:
        logger.error(f"Unlock failed: {e}")
        click.echo(click.style(f"✗ Unlock failed: {e}", fg='red'))
        raise SystemExit(1)


if __name__ == '__main__':
    cli()