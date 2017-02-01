'''
Created on Apr 3, 2016

@author: riccardo
'''
import click
from gfzreport.web.app import get_app


@click.command()
@click.option('-p', '--port', default=None,  # callback=click_get_wildcard_iterator,
              help=("The port where to run the application. Defaults to 5000"))
@click.option('-d', '--debug', default=None,
              help='The path to the FILE of the data availability image')
def main(port, debug):
    app = get_app()
    if not debug and not port:
        app.run()
    elif debug:
        app.run(debug=debug)  # , use_reloader=False)  # avoid debugger starting twice
    elif port:
        app.run(port=port)
    else:
        app.run(port=port, debug=debug)

if __name__ == '__main__':
    main()
