import argparse
import asyncio
import random
import logging
import os


BLOCKED = []
TASKS = []


async def main(host, port, blacklist, log):

    global BLOCKED

    logging.basicConfig(
        filename=log,
        level=logging.ERROR,
        encoding="utf-8",
        format="[%(asctime)s][%(levelname)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    BLOCKED = [line.rstrip().encode()
               for line in open(blacklist, "r", encoding="utf-8")]

    os.system('')
    print('''
\033[92m`7MN.   `7MF'          `7MM"""Yb.   `7MM"""Mq. `7MMF'
  MMN.    M              MM    `Yb.   MM   `MM.  MM
  M YMb   M   ,pW"Wq.    MM     `Mb   MM   ,M9   MM
  M  `MN. M  6W'   `Wb   MM      MM   MMmmdM9    MM
  M   `MM.M  8M     M8   MM     ,MP   MM         MM
  M     YMM  YA.   ,A9   MM    ,dP'   MM         MM
.JML.    YM   `Ybmd9'  .JMMmmmdP'   .JMML.     .JMML.\033[0m
          ''')
    print("Enjoy watching! / Наслаждайтесь просмотром!".center(50))
    print(f"Proxy is running on {host}:{port}".center(50))
    print('\n')
    print('\033[92m[INFO]:\033[97m To stop the proxy, press Ctrl+C'.center(50))
    print('\033[92m[INFO]:\033[97m Logging is in progress. You can see the list of errors in the file '
          f'{log}'.center(50))

    server = await asyncio.start_server(new_conn, host, port)
    await server.serve_forever()


async def pipe(reader, writer):

    while not reader.at_eof() and not writer.is_closing():
        try:
            writer.write(await reader.read(1500))
            await writer.drain()
        except Exception as e:
            logging.error(e)
            print(f'\033[93m[NON-CRITICAL]:\033[97m {e}\033[0m')
            break

    writer.close()


async def new_conn(local_reader, local_writer):

    http_data = await local_reader.read(1500)

    if not http_data:
        local_writer.close()
        return

    try:
        type, target = http_data.split(b"\r\n")[0].split(b" ")[0:2]
        host, port = target.split(b":")
    except Exception as e:
        logging.error(e)
        print(f'\033[93m[NON-CRITICAL]:\033[97m {e}\033[0m')
        local_writer.close()
        return

    if type != b"CONNECT":
        local_writer.close()
        return

    local_writer.write(b"HTTP/1.1 200 OK\n\n")
    await local_writer.drain()

    try:
        remote_reader, remote_writer = await asyncio.open_connection(host, port)
    except Exception as e:
        logging.error(e)
        print(f'\033[93m[NON-CRITICAL]:\033[97m {e}\033[0m')
        local_writer.close()
        return

    if port == b"443":
        await fragment_data(local_reader, remote_writer)

    TASKS.append(asyncio.create_task(pipe(local_reader, remote_writer)))
    TASKS.append(asyncio.create_task(pipe(remote_reader, local_writer)))


async def fragment_data(local_reader, remote_writer):

    try:
        head = await local_reader.read(5)
        data = await local_reader.read(2048)
    except Exception as e:
        logging.error(e)
        print(f'\033[93m[NON-CRITICAL]:\033[97m {e}\033[0m')
        local_reader.close()
        return

    parts = []

    if all(data.find(site) == -1 for site in BLOCKED):
        remote_writer.write(head + data)
        await remote_writer.drain()
        return

    host_end_index = data.find(b"\x00")
    if host_end_index != -1:
        parts.append(
            bytes.fromhex("1603")
            + bytes([random.randint(0, 255)])
            + int(host_end_index + 1).to_bytes(2, byteorder="big")
            + data[: host_end_index + 1]
        )
        data = data[host_end_index + 1:]

    while data:
        part_len = random.randint(1, len(data))
        parts.append(
            bytes.fromhex("1603")
            + bytes([random.randint(0, 255)])
            + int(part_len).to_bytes(2, byteorder="big")
            + data[0:part_len]
        )
        data = data[part_len:]

    remote_writer.write(b"".join(parts))
    await remote_writer.drain()

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "--host",
        default="127.0.0.1",
        help="The host to run the proxy on",
    )
    argparser.add_argument(
        "--port",
        default=8881,
        help="The port to run the proxy on",
    )
    argparser.add_argument(
        "--blacklist",
        default="blacklist.txt",
        help="The path to the blacklist file",
    )
    argparser.add_argument(
        "--log",
        default="errors.log",
        help="The path to the log file",
    )
    args = argparser.parse_args()

    asyncio.run(main(
        host=args.host,
        port=args.port,
        blacklist=args.blacklist,
        log=args.log))
