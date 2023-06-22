from argparse import ArgumentParser
import datetime
import subprocess
import time


def parse_args():
    parser = ArgumentParser()
    
    parser.add_argument('--debug', '-d', action='store_true')
    
    return parser.parse_args()


def handle_debug(debug_on, msg):
    if debug_on:
        print(f'DEBUG -- {msg}')


def get_interval_msg(timestamp, total_pings, lost_pings, response_times):
    packet_loss = 0.00 if lost_pings == 0 else (lost_pings / total_pings) * 100
    avg_response = 0 if len(response_times) == 0 else sum(response_times) / len(response_times)
    msg = f'{timestamp}: Checkpoint, packet loss = {packet_loss}%; avg response = {avg_response}ms'
    return msg
    

def record_packet_loss(debug=False):
    outfile = 'packet_loss_log.txt'
    response_times = []
    total_pings = 0
    lost_pings = 0
    
    with open(outfile, 'w') as fp:
        ping_process = subprocess.Popen(
            ['ping', '-t', '8.8.8.8'],
            stdout=subprocess.PIPE
        )
        
        try:
            interval_time = time.time()
            while True:
                ping_output = ping_process.stdout.readline().decode('utf-8').lower().strip()
                handle_debug(debug, f'Original: {ping_output}')
                if 'pinging' in ping_output or 'statistics' in ping_output or not ping_output:
                    continue
                total_pings += 1

                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                parsed = parse_ping_output(ping_output)
                handle_debug(debug, f'Parsed: {parsed}')
                if parsed is None:
                    lost_pings += 1
                    msg = f'{timestamp}: Lost packet\n'
                    fp.write(msg)
                    fp.flush()
                    handle_debug(debug, msg)
                else:
                    response_times.append(parsed)
            
                if time.time() - interval_time > 1800:
                    msg = get_interval_msg(timestamp, total_pings, lost_pings, response_times)
                    fp.write(f'{msg}\n')
                    fp.flush()
                    print(msg)
                    total_pings = 0
                    lost_pings = 0
                    response_times = []
                    interval_time = time.time()
        except KeyboardInterrupt as err:
            ping_process.terminate()
            ping_process.wait()
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            msg = get_interval_msg(timestamp, total_pings, lost_pings, response_times)
            msg = f'{msg} -- +{time.time() - interval_time}\n'
            fp.write(msg)
            fp.flush()
            print(msg)
            
        

def parse_ping_output(ping_output):
    retval = None
    if 'reply from' in ping_output and 'time=' in ping_output:
        start = ping_output.find('time=')
        end = ping_output.find('ms', start)
        substr = ping_output[start+5:end]
        try:
            retval = float(substr)
        except ValueError as err:
            pass
    return retval


if __name__ == '__main__':
    args = parse_args()
    record_packet_loss(args.debug)