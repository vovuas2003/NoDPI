import random
import asyncio
import sys

DEFAULT_IP = "127.0.0.1"
DEFAULT_PORT = 8080

BLOCKED = []
TASKS = []

def main():
    global BLOCKED
    args = sys.argv
    if (len(args) == 2 or len(args) == 4) and args[-1] == "1337":
        if len(args) == 4:
            try:
                host = args[1]
                port = int(args[2])
            except:
                host = DEFAULT_IP
                port = DEFAULT_PORT
        else:
            host = DEFAULT_IP
            port = DEFAULT_PORT
        urls = ["youtube.com", "youtu.be", "yt.be", "googlevideo.com", "ytimg.com", "ggpht.com", "gvt1.com", "youtube-nocookie.com", "youtube-ui.l.google.com", "youtubeembeddedplayer.googleapis.com", "youtube.googleapis.com", "youtubei.googleapis.com", "yt-video-upload.l.google.com", "wide-youtube.l.google.com"]
        BLOCKED = [x.encode() for x in urls]
        print(f"TBou uHTepHeT nopTaJI: {host}")
        print(f"TBo9 raBaHb: {port}")
        print("blackjack cnucoK 3aXapgKo}|{eH")
    else:
        try:
            with open("blacklist.txt", "r", encoding = "utf-8") as f:
                BLOCKED = [line.rstrip().encode() for line in f]
            print(f"Only blacklist.txt fragmentation ({len(BLOCKED)} URLs)!")
        except:
            BLOCKED = None
            print("Fragmentation for all HTTPS traffic (TCP port 443), can't open blacklist.txt!")
        print()
        if len(args) == 3:
            try:
                host = args[1]
                port = int(args[2])
                print(f"Your proxy settings: ip {host} and port {port}")
            except:
                host = DEFAULT_IP
                port = DEFAULT_PORT
                print(f"Incorrect options for ip or port, using default {DEFAULT_IP} {DEFAULT_PORT}")
        else:
            host = DEFAULT_IP
            port = DEFAULT_PORT
            print("Using default ip and port for proxy server, it is equal to:")
            print(f"{args[0]} {DEFAULT_IP} {DEFAULT_PORT}")
            print("Add command line options to change these settings.")
    print()
    print("Starting proxy server, ctrl+c to shutdown.")
    asyncio.run(almost_main(host, port))

async def almost_main(host, port):
    server = await asyncio.start_server(new_conn, host, port)
    await server.serve_forever()

async def pipe(reader, writer):
    while not reader.at_eof() and not writer.is_closing():
        try:
            writer.write(await reader.read(1500))
            await writer.drain()
        except:
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
    except:
        local_writer.close()
        return
    if type != b"CONNECT":
        local_writer.close()
        return
    local_writer.write(b"HTTP/1.1 200 OK\n\n")
    await local_writer.drain()
    try:
        remote_reader, remote_writer = await asyncio.open_connection(host, port)
    except:
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
    except:
        local_reader.close()
        return
    parts = []
    if BLOCKED != None:
        if all(data.find(site) == -1 for site in BLOCKED):
            remote_writer.write(head + data)
            await remote_writer.drain()
            return
    host_end_index = data.find(b"\x00")
    if host_end_index != -1:
        parts.append(bytes.fromhex("1603") + bytes([random.randint(0, 255)]) + int(host_end_index + 1).to_bytes(2, byteorder="big") + data[: host_end_index + 1])
        data = data[host_end_index + 1:]
    while data:
        part_len = random.randint(1, len(data))
        parts.append(bytes.fromhex("1603") + bytes([random.randint(0, 255)]) + int(part_len).to_bytes(2, byteorder="big") + data[0:part_len])
        data = data[part_len:]
    remote_writer.write(b"".join(parts))
    await remote_writer.drain()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("Goodbye!")
    except Exception:
        print()
        print("Unknown error, emergency exit!")
        print("Double check the format of your custom ip and port settings in command line options if this message appears right after proxy startup!")
