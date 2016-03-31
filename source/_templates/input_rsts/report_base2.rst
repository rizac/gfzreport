{% if gfz_logo_path %}
.. image:: {{ gfz_logo_path }}
   :align: left
   :height: 3em

{% endif %}
{% if gfz_wordmark_path %}
.. image:: {{ gfz_wordmark_path }}
   :align: right
   :height: 3em

{% endif %}
{% if authors_text %}
:authors: {{ authors_text }}

{% endif %}
{% if include_date %}
:date: 2003/06/05

{% endif %}
{% if revision_text %}
:revision: {{ revision_text }}

{% endif %}
{% if abstract_text %}
:abstract:

{{ abstract_text }}

{% endif %}
{% if copyright_text %}
:copyright: {{ copyright_text }}

{% endif %}

# {{ title_text }}

{% if network_map_csv_path %}
## Network

.. map-figure:: {{ network_map_csv_path }}
   :name_key: Name
   :lat_key: Lat
   :lon_key: Lon 
   :align: center
   
.. {{ network_map_caption }}
{% endif %}

{% if stations_table_csv_path %}
## Stations

.. csv-table:: 
   :file: {{ stations_table_csv_path }}
{% endif %}

{% if data_availability_img_path %}
## Data Availability

.. figure:: {{ data_availability_img_path }}
   :align: center
   :width: 100%

   {{ data_availability_img_caption }}
{% endif %}

{% if gps_timing_quality_img_path %}
## GPS Timing Quality

.. figure:: {{ gps_timing_quality_img_path }}
   :align: center
   :width: 100%

   {{ gps_timing_quality_img_caption }}
{% endif %}

{% if pdfs_path %}
## PDF's

.. imgages-grid:: {{ pdfs_path }}
   :columns: "_HHE*.pdf" _HHN*.pdf _HHZ*.pdf
{% endif %}

{% if appendix_text %}
## Appendix

{{ appendix_text }}
{% endif %}