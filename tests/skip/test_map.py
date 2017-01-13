'''
Created on Jan 12, 2017

@author: riccardo
'''
# import matplotlib
import tempfile
import time
# matplotlib.use('TkAgg')  # this is for mac, remove / change if needed
from itertools import product
from reportbuild.map import plotmap
import matplotlib.pyplot as plt
from subprocess import call
import os


def show(fig, asfile=True):
    if asfile:
        with tempfile.NamedTemporaryFile(suffix='.png', delete=True) as tmpf:
            name = tmpf.name
            fig.savefig(tmpf.name)
            # copy file to another location
            call(['open', name])
            # this makes work all the stuff, as we have the time to open the file before
            # removing it (when we get out of this with):
            time.sleep(5)
        if os.path.isfile(name):
            os.remove(name)
    else:
        plt.show(block=True)

if __name__ == '__main__':
    lonslats = list(product([-50, 78.1], [49,79, 78]))  # [-20, -22, -21]))
    labels = [str(x) for x in lonslats]
    lonz, latz = zip(*lonslats)
    f = plotmap(lonz, latz, markers=['o', '^', '^', 's', 's', 's'],
                map_margins="10deg", fig_margins="1,3,8,1",
                labels=labels, legend_labels=['circle', 'tri', None, 'sq1', 'sq2', None],
                parallels_linewidth=1, meridians_linewidth=1, arcgis_image_xpixels=1500,
                arcgis_image_dpi=96, legend_loc='bottom')  # , basemap_background_type = 'shadedrelief')  # , show=True)
    show(f)
    pass