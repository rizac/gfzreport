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
    import csv
#     labels, lats, lons, markers, colors, legends = [], [], [], [], [], []
#     with open(os.path.join(os.path.dirname(__file__), 'map.csv')) as csvfile:
#         reader = csv.DictReader(csvfile)
#         for row in reader:
#             labels.append(row['Name'])
#             lats.append(row['Lat'])
#             lons.append(row['Lon'])
#             markers.append(row['Marker'])
#             colors.append(row['Color'])
#             
#             # print(row['first_name'], row['last_name'])
#             
#     f = plotmap(lons, lats, markers=markers, colors=colors, labels=labels,
#                 arcgis_service='xxx', labels_h_offset="-0.1deg", labels_v_offset="0.2deg",
#                 sizes=50, fontsize=10)
#     show(f)


    labels, lats, lons, markers, colors, legends = [], [], [], [], [], []
    with open(os.path.join(os.path.dirname(__file__), 'map_with_legend.csv')) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            labels.append(row['Name'])
            lats.append(row['Lat'])
            lons.append(row['Lon'])
            markers.append(row['Marker'])
            colors.append(row['Color'])
            legends.append(row['Legend'])
            # print(row['first_name'], row['last_name'])
            
    f = plotmap(lons, lats, markers=markers, colors=colors, labels=labels,
                legendlabels = legends,
                labels_h_offset="-0.04deg", labels_v_offset="0.04deg",
                sizes=50, fontsize=8, fig_margins="1,2,9,0", legend_ncol=2,
                arcgis_xpixels=1500,)
#                  map_margins="-0.1deg",
#                 arcgis_service='xxx', )
    show(f)

#     lonslats = list(product([-50, 78.1], [49,79, 78]))  # [-20, -22, -21]))
#     labels = [str(x) for x in lonslats]
#     lonz, latz = zip(*lonslats)
#     f = plotmap(lonz, latz, markers=['o', '^', '^', 's', 's', 's'],
#                 map_margins="10deg", fig_margins="1,3,18,1", fontweight='regular', # 'extra bold',
#                 fontcolor='k', arcgis_xpixels=400,
#                 labels=labels, legendlabels=['circle', 'tri', None, 'sq1', 'sq2', None],
#                 parallels_linewidth=1, meridians_linewidth=1,
#                 legend_pos='bottom', 
#                 legendlabels_fontsize=21,
#                 arcgis_service='xxx')  # , basemap_background_type = 'shadedrelief')  # , show=True)
#     show(f)
    pass