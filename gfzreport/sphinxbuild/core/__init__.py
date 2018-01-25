def touni(obj):
    '''python2-3 compatible function to convert to unicode,
    as many nodes elements expect unicodes'''
    return obj.decode('utf8') if isinstance(obj, bytes) else obj