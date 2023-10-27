from distributions.io.stream import (
    open_compressed, protobuf_stream_load)
from loom.cFormat import assignment_stream_load
from loom.util import get_message, protobuf_to_dict
from parsable import parsable
import json
import os

@parsable
def loom_to_json(filename):
    ''' Convert a loom file to a json file. '''
    name = filename.split("/")[-1].split(".")[0]
    output_filename = "/".join(filename.split("/")[:-1]) + "/{}.json".format(name)

    parts = os.path.basename(filename).split('.')
    if parts[-1] in ['gz', 'bz2']:
        parts.pop()

    try:
        if parts[0] == "assign":
            message_dict = parse_assign(filename)
        elif parts[-1] == "pb":
            message_dict = parse_pb(filename)
        elif parts[-1] == "pbs":
            message_dict = parse_pbs(filename)
        else:
            raise ValueError('Unknown protocol: {}'.format(filename))
 
    except AssertionError:
        # empty message
        return

    with open(output_filename, "w") as f:
        json.dump(message_dict, f)

def parse_assign(filename):
    stream = assignment_stream_load(filename)

    assignments = {
        a.rowid: [a.groupids(k) for k in xrange(a.groupids_size())]
        for a in stream
    }
    rowids = sorted(assignments)
    n_k = len(next(iter(assignments.values())))
    return {
        k: [assignments[rowid][k] for rowid in rowids]
        for k in xrange(n_k)
    }


def parse_pb(filename):
    message = get_message(filename)
    with open_compressed(filename) as f:
        message.ParseFromString(f.read())
        return protobuf_to_dict(message)

def parse_pbs(filename):
    message = get_message(filename)
    string_stream = [s for s in protobuf_stream_load(filename)]
    string = ''.join(string_stream)
    message.ParseFromString(string)
    return protobuf_to_dict(message)


if __name__ == "__main__":
    parsable()