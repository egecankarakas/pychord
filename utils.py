from hashlib import sha1

import settings


# Check if element exist over chord ring's arc
def arc_contains(start, stop, element, start_included=False, end_included=False):
    if end_included and start == stop:
        return True
    if stop < start:
        if element < start:
            element += 1 << settings.NETWORK_SIZE
        stop += 1 << settings.NETWORK_SIZE
    if start_included:
        if end_included:
            return start <= element <= stop
        else:
            return start <= element < stop
    else:
        if end_included:
            return start < element <= stop
        else:
            return start < element < stop


def get_node_id(ip):
    hash_value = sha1()
    hash_value.update(ip.encode())
    hash_value.update(settings.CHORD_PORT.to_bytes(3, "big"))
    nid = int.from_bytes(
        hash_value.digest(), "big"
    ) % (1 << settings.NETWORK_SIZE)  # SHA-1 result is casted to nid (node id)
    return nid
