'''
Utilities for creating hashes from various python objects
WARNING: DEPRECATED: will be removed in the future
Created on Mar 23, 2016

@author: riccardo


'''
from core.utils import isnumpy, isstr


def flattened_list(*args, **kw):
    """
        Flattens the arguments returning a list with all sub-elements (if any) of arguments,
        extracted recursively (dicts are pre-processed converting them to lists, in the order of
        their keys. numpy arrays are pre-processed by converting them to their python equivalent
        type)
        :param args: a ordered sequence of objects
        :param kw: a key:value sequence of parameters
        :return: a list of all arguments, extracted recursively
        :Example:
        flattened_list(1, {'c':9, 'a':[1, '2']}) = [1, 'a', 1, '2', 'c', 9]
    """
    args = list(args)  # args is a tuple

    for key in sorted(kw):
        args.append(key)
        args.append(kw[key])

    ret_list = []

    while len(args):
        val = args.pop(0)
        if isnumpy(val):
            val = val.tolist()
            # note: to list converts also "scalars" to their python equivalent, so val might be
            # e.g., a string now, or a list, or a number, etc
            # http://stackoverflow.com/questions/4565749/how-detect-length-of-a-numpy-array-with-only-one-element)
        if isstr(val) or not hasattr(val, "__iter__"):
            ret_list.append(val)
            continue

        if not type(val) == list:
            if type(val) == dict:
                # flatten the dict into list. See
                # http://stackoverflow.com/questions/1679384/converting-python-dictionary-to-list
                val = reduce(lambda x, y: x+y, ([k, val[k]] for k in sorted(val)), [])
            else:
                val = list(val)

        args = val + args

    return ret_list


def get_hash(val):
    """
        General method which extracts the hash of val, which can be (almost) any python object,
        including numpy arrays. This mkethod extracts recursively any value if val and then
        calculates the hash of the resulting tuple.
        Note that this method ALMOST guarantees that two objects with the
        same value(s) are the same same. However, for large number of items the hash truncates its
        digits and thus this is not true anymore
    """
    flattened_tuple = tuple(flattened_list(val))
    return hash(flattened_tuple)


# def flatten_old(val):
#     """
#         Flattens val, building a list of all its sub-elements recursively (if any) i.e. extracts
#         all sub-items recursively (if any). Returns the list and the hashes of all its elements, as
#         a list
#         :param val: a python object
#         :return: a tuple of two lists, the first denoting all items in val (recusrively), the second
#         their hash, or None if the item cannot be hashable
#         :Example:
#         flatten({'a':9, c:[1,2]})
#     """
#     def isnumpy(val):
#         return type(val).__module__ == np.__name__
# 
#     try:
#         if isnumpy(val):
#             val = val.tolist()
#             # Note: in this case it might be that val is NOT a python list, e.g. np.array(5). See
#             # http://stackoverflow.com/questions/4565749/how-detect-length-of-a-numpy-array-with-only-one-element)
#         hsh = hash(val)
#         return [val], [hsh]
#     except TypeError:
#         if hasattr(val, "__iter__"):
#             if type(val) == dict:
#                 lst = []
#                 for key in sorted(val):
#                     lst.append(key)
#                     lst.append(val[key])
#             else:
#                 lst = val
# 
#             new_vals = []
#             new_hsh = []
#             for itm in lst:
#                 val, hsh = flatten(itm)
#                 new_vals.extend(v for v in val)
#                 new_hsh.extend(h for h in hsh)
#             return new_vals, new_hsh
#         else:
#             return [val], [None]

if __name__ == "__main__":
    print str(hash(tuple(flattened_list(1, {'c':9, 'a':[1,2]}))) == hash(tuple(flattened_list({'a':[1,2], 'c':9}, 1))))
    a1 = [1, {'c':9, 'a':[1,2]}]
    a2 = [1, {'c':9, 'a':[1,2]}]
    print get_hash(a1) == get_hash(a2)