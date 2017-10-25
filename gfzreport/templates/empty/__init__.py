'''
Created on Jul 24, 2017

@author: riccardo
'''
import click
import os
from gfzreport.templates.utils import cp_template_tree, validate_outdir
import sys


@click.command()
@click.option('-o', '--out_path', default=None, callback=validate_outdir,
              help=("The output path. The destination directory "
                    "will be a directory in this path with name [NETWORK]_[STATION]. "
                    "The destination directory must *not* exist, or the program will exit. "
                    "If this program is deployed on a web server, this is the DATA_DIR "
                    "environment variable provided for the network report (if deployed on "
                    "Apache, see relative .wsgi file)"))
@click.option("--mv", is_flag=True, default=False,
              help=("Move all specified files instead of copying"
                    "them (default False, i.e. missing)"))
@click.option("--noprompt", is_flag=True, default=False, is_eager=True,  # <- exec it first. Used?
              help=("Do not ask before proceeding if the user wants to write to out_path. "
                    "The default, when this flag is missing, is False"
                    "(always ask before writing)"))
def main(out_path, mv, noprompt):
    """
    Generates the report folder for an "empty" report
    """
    # remember: the doc above is shown when calling --help. Arguments DO NOT ACCEPT HELP, THUS
    # IT MUST BE WRITTEN THERE!!

    # FIXME: IMPORTANT: unix shell expands wildcards automatically, so we might avoid the glob
    # module. Fine, BUT CLICK DOES NOT SUPPORT MULTIPLE (UNDEFINED) OPTIONS
    # So for the moment we DISABLE that option
    #
    # Moreover, if we ever re-implement it in the futre, remember that windows does not expand
    # wildcards
    # (http://stackoverflow.com/questions/12501761/passing-multple-files-with-asterisk-to-python-shell-in-windows)
    try:
        sys.exit(run(out_path, mv, not noprompt))
    except Exception as exc:
        print("Aborted: %s" % str(exc))
        sys.exit(1)


def run(out_path, mv, confirm):
    in_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sphinx")
    with cp_template_tree(in_path, out_path, confirm) as _data_outdir:
        pass  # copy the folder and the sub-folders, nothing else to do

    return 0


if __name__ == '__main__':
    main()  # pylint:disable=no-value-for-parameter
