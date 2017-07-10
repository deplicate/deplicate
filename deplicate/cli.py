# -*- coding: utf-8 -*-
#
#          _/                   _/ _/                     _/
#     _/_/_/   _/_/   _/_/_/   _/     _/_/_/    _/_/_/ _/_/_/_/   _/_/
#  _/    _/ _/_/_/_/ _/    _/ _/ _/ _/       _/    _/   _/     _/_/_/_/
# _/    _/ _/       _/    _/ _/ _/ _/       _/    _/   _/     _/
#  _/_/_/   _/_/_/ _/_/_/   _/ _/   _/_/_/   _/_/_/     _/_/   _/_/_/
#                 _/
#                _/

from __future__ import absolute_import

import click

from .deplicate import deplicate


@click.command()
@click.argument('paths',
                type=click.Path(exists=True),
                nargs=-1)
# @click.option('--verbose', '-v',
#               count=True,
#               help='Verbose mode (repeat to increase verbosity).')
@click.option('--minsize', '-s',
              type=click.IntRange(min=0, clamp=True),
              default=None,
              help='Minimum size of files to include in scanning.')
@click.option('--include', '-i',
              help='Wildcard pattern of files to include in scanning.')
@click.option('--exclude', '-e',
              help='Wildcard pattern of files to exclude from scanning.')
@click.option('--comparename', '-n',
              is_flag=True,
              help='Check file name.')
@click.option('--comparemtime', '-m',
              is_flag=True,
              help='Check file modification time.')
@click.option('--compareperms', '-p',
              is_flag=True,
              help='Check file mode (permissions).')
@click.option('--recursive', '-r',
              is_flag=True,
              help='Scan directory recursively.')
@click.option('--followlinks',
              is_flag=True,
              help='Follow symbolic links pointing to directory.')
@click.option('--scanlinks',
              is_flag=True,
              help='Scan symbolic links pointing to file.')
@click.option('--scanempties',
              is_flag=True,
              help='Scan empty files.')
@click.option('--scansystems/--ignoresystems',
              default=True,
              help='Scan OS files.')
@click.option('--scanarchived/--ignorearchived',
              default=True,
              help='Scan archived files.')
@click.option('--scanhidden/--ignorehidden',
              default=True,
              help='Scan hidden files.')
@click.version_option()
def main(**kwgs):
    """
    Advanced Duplicate File Finder for Python

    Copyright 2017 Walter Purcaro <vuolter@gmail.com>
    """

    # verbose = kwgs.pop('verbose')
    result = deplicate(**kwgs)
    click.echo(result)
