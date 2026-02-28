# coroutine_checkpoint.py

import json

CHECKPOINT_FILE = 'checkpoint.json'
DATA_FILE = 'numbers.txt'

def load_checkpoint():
    try:
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'offset': 0, 'running_sum': 0}

def save_checkpoint(offset, running_sum):
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump({'offset': offset, 'running_sum': running_sum}, f)

def number_stream_coroutine(filename, start_offset):
    with open(filename, 'r') as f:
        f.seek(start_offset)
        while line := f.readline():
            pos = f.tell()
            number = int(line.strip())
            checkpoint = yield pos, number
            if checkpoint:
                yield 'checkpoint', pos

def process():
    state = load_checkpoint()
    offset = state['offset']
    running_sum = state['running_sum']

    stream = number_stream_coroutine(DATA_FILE, offset)
    pos = offset  # Initialize to current offset (IMPORTANT)

    try:
        pos, number = next(stream)
    except StopIteration:
        save_checkpoint(pos, running_sum)
        print("Final sum:", running_sum)
        return

    while True:
        running_sum += number
        do_checkpoint = (pos % 10000 < 50)
        try:
            result = stream.send(do_checkpoint)
        except StopIteration:
            break
        if isinstance(result, tuple) and result[0] == 'checkpoint':
            save_checkpoint(result[1], running_sum)
            try:
                pos, number = next(stream)
            except StopIteration:
                break
        else:
            pos, number = result

    save_checkpoint(pos, running_sum)
    print("Final sum:", running_sum)

if __name__ == '__main__':
    process()
