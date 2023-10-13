from loom.util import get_message, protobuf_to_dict
from distributions.io.stream import open_compressed, protobuf_stream_load
from parsable import parsable
import json
import os

@parsable
def loom_to_json(filename):
    ''' Convert a loom file to a json file. '''
    message = parse_message(filename)
    try:
        message_dict = protobuf_to_dict(message)
    except AssertionError:
        # empty message
        return

    # remove characters after the first dot after the last slash
    name = filename.split("/")[-1].split(".")[0]
    output_filename = "/".join(filename.split("/")[:-1]) + "/{}.json".format(name)

    with open(output_filename, "w") as f:
        json.dump(message_dict, f, indent=4)

def parse_message(filename):
    parts = os.path.basename(filename).split('.')
    if parts[-1] in ['gz', 'bz2']:
        parts.pop()
    protocol = parts[-1]
    if protocol == 'pb':
        message = get_message(filename)
        with open_compressed(filename) as f:
            message.ParseFromString(f.read())
            return message
    elif protocol == 'pbs':
        message = get_message(filename)
        string_stream = [s for s in protobuf_stream_load(filename)]
        string = ''.join(string_stream)
        message.ParseFromString(string)
        return message
    else:
        raise ValueError('Unknown protocol: {}'.format(protocol))
    


if __name__ == "__main__":
    parsable()