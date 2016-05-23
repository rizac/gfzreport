'''
Created on May 20, 2016

@author: riccardo
'''
import os


def freeze(path):
    dic = {}
    for root, dirnames, filenames in os.walk(path):
        for fname in filenames:
            fpath = os.path.abspath(os.path.join(root, fname))
            stat = os.stat(fpath)
            dic[fpath] = (stat[8], stat[6])
    return dic


def get_new_files(path, freezed_dict):
    new_dict = freeze(path)
    ret_dict = {}
    for fpath in new_dict:
        if fpath not in freezed_dict or new_dict[fpath] > freezed_dict[fpath]:
            ret_dict[fpath] = new_dict[fpath]
    return ret_dict
