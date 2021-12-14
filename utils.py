import settings


# Check if element exist over chord ring's arc
def arc_contains(start,stop,element,start_included=False,end_included=False):
    if stop < start:
        if element < start:
            element += 1 << settings.NETWORK_SIZE
        stop += 1 << settings.NETWORK_SIZE
    if start_included:
        if end_included:
            return start<=element<=stop
        else:
            return start<=element<stop
    else:
        if end_included:
            return start<element<=stop
        else:
            return start<element<stop
