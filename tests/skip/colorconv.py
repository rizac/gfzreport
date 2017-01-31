'''
Created on Jan 11, 2017

@author: riccardo
'''

# def tofloat(rgbint):
#     return rgbint / 255.0
# 
# 
# def toint(floatval):
#     return int(floatval * 255 + 0.5)
# 
# 
# def tohex(floatval):
#     return hex(toint(floatval))[2:].upper().zfill(2)
import numpy as np

def toint(hexval):
    return int(hexval, 16)


def torgba(html_str):
    """Converts html_str into a tuple of rgba colors in 0, 255 if alpha channel is not
    specified, or [0,1] otherwise
    :param html_str: a valid html string in hexadecimal format.
    Can have length 4, 7 or 9 such as #F1a, #fa98e3, #fc456a09
    :raise: ValueError if html_str is invalid, TypeError if not a string
    """
    if len(html_str) not in (4, 7, 9) or not html_str[0] == '#':
        raise ValueError("'%s' invalid html string" % html_str)
    elif len(html_str) == 4:
        rgb = [html_str[i:i+1]*2 for i in xrange(1, len(html_str))]
    else:
        rgb = [html_str[i:i+2] for i in xrange(1, len(html_str), 2)]

    rgb = np.array([int(r, 16) for r in rgb])

    if len(html_str) == 9:
        # convert in this case to 0,1:
        rgb = np.true_divide(rgb, 255)

    return rgb



if __name__ == "__main__":
    for html in ("#fff", "#FF0", "#FF00FF", "#ff00ffff", "#ff00ff00", 45, 
                 "#efa9f10F", "#TYR"):
        print html + " " +str(torgba(html))