#!/usr/bin/env python3

import argparse
import asyncio
import random
import logging
import os
import sys
from datetime import datetime

__version__ = "1.6"

os.system("")


class ProxyServer:

    def __init__(self, host, port, blacklist, log, verbose):

        self.host = host
        self.port = port
        self.blacklist = blacklist
        self.log_file = log
        self.verbose = verbose

        self.total_connections = 0
        self.allowed_connections = 0
        self.blocked_connections = 0
        self.traffic_in = 0
        self.traffic_out = 0

        self.blocked = []
        self.tasks = []
        self.server = None

        self.setup_logging()
        self.load_blacklist()

    def setup_logging(self):
        """
        Set up the logging configuration.

        The logging level is set to ERROR and the log messages are written to the
        file specified by the log_file parameter. The log format is
        [%(asctime)s][%(levelname)s]: %(message)s and the date format is
        %Y-%m-%d %H:%M:%S.
        """
        logging.basicConfig(
            filename=self.log_file,
            level=logging.ERROR,
            encoding="utf-8",
            format="[%(asctime)s][%(levelname)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def load_blacklist(self):
        """
        Load the blacklist from the specified file.
        """
        if not os.path.exists(self.blacklist):
            print(f"\033[91m[Error]: File {self.blacklist} not found\033[0m")
            logging.error("File %s not found", self.blacklist)
            sys.exit(1)

        with open(self.blacklist, "r", encoding="utf-8") as f:
            self.blocked = [line.rstrip().encode() for line in f]

    async def run(self):
        """
        Start the proxy server and run it until it is stopped.

        This method starts the proxy server by calling
        `asyncio.start_server` with the `handle_connection` method as the
        protocol handler. The server is then started with the `serve_forever`
        method.
        """
        self.print_banner()
        asyncio.create_task(self.display_stats())
        self.server = await asyncio.start_server(
            self.handle_connection, self.host, self.port
        )
        await self.server.serve_forever()

    def print_banner(self):
        """
        Print a banner with the NoDPI logo and information about the proxy.
        """
        print(
            '''
\033[92m`7MN.   `7MF'          `7MM"""Yb.   `7MM"""Mq. `7MMF'
  MMN.    M              MM    `Yb.   MM   `MM.  MM
  M YMb   M   ,pW"Wq.    MM     `Mb   MM   ,M9   MM
  M  `MN. M  6W'   `Wb   MM      MM   MMmmdM9    MM
  M   `MM.M  8M     M8   MM     ,MP   MM         MM
  M     YMM  YA.   ,A9   MM    ,dP'   MM         MM
.JML.    YM   `Ybmd9'  .JMMmmmdP'   .JMML.     .JMML.\033[0m
        '''
        )
        print(f"\033[92mVersion: {__version__}".center(50))
        print("\033[97m"+"Enjoy watching! / Наслаждайтесь просмотром!".center(50))
        print(f"Proxy is running on {self.host}:{self.port}".center(50))
        print("\n")
        print(
            f"\033[92m[INFO]:\033[97m Proxy started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(
            f"\033[92m[INFO]:\033[97m Blacklist contains {len(self.blocked)} domains")
        print(
            "\033[92m[INFO]:\033[97m To stop the proxy, press Ctrl+C twice")
        print(
            "\033[92m[INFO]:\033[97m Logging is in progress. You can see the list of errors in the file "
            f"{self.log_file}")

    async def display_stats(self):
        """
        Display the current statistics of the proxy server.
        """
        while True:
            await asyncio.sleep(1)
            stats = (
                f"\033[92m[STATS]:\033[0m "
                f"\033[97mConnections: \033[93m{self.total_connections}\033[0m | "
                f"\033[97mMissing: \033[92m{self.allowed_connections}\033[0m | "
                f"\033[97mUnblocked: \033[91m{self.blocked_connections}\033[0m | "
                f"\033[97mTraffic In: \033[96m{self.format_size(self.traffic_in)}\033[0m | "
                f"\033[97mTraffic Out: \033[96m{self.format_size(self.traffic_out)}\033[0m"
            )
            print('\u001b[2K'+stats, end='\r', flush=True)

    @staticmethod
    def format_size(size):
        """
        Convert a size in bytes to a human-readable string with appropriate units.
        """
        units = ['B', 'KB', 'MB', 'GB']
        unit = 0
        while size >= 1024 and unit < len(units)-1:
            size /= 1024
            unit += 1
        return f"{size:.2f} {units[unit]}"

    async def handle_connection(self, reader, writer):
        """
        Handle a connection from a client.

        This method is called when a connection is accepted from a client. It reads
        the initial HTTP data from the client and tries to parse it as a CONNECT
        request. If the request is valid, it opens a connection to the target
        server and starts piping data between the client and the target server.
        """
        self.total_connections += 1
        http_data = await reader.read(1500)
        if not http_data:
            writer.close()
            return

        try:
            headers = http_data.split(b"\r\n")[0].split(b" ")
            conn_type = headers[0]
            target = headers[1]
            host, port = target.split(b":")
        except Exception as e:
            logging.error(e)
            if self.verbose:
                print(f"\033[93m[NON-CRITICAL]:\033[97m {e}\033[0m")
            writer.close()
            return

        if conn_type != b"CONNECT":
            writer.close()
            return

        writer.write(b"HTTP/1.1 200 OK\n\n")
        await writer.drain()

        try:
            remote_reader, remote_writer = await asyncio.open_connection(
                host.decode(), port.decode()
            )
        except Exception as e:
            logging.error(e)
            if self.verbose:
                print(f"\033[93m[NON-CRITICAL]:\033[97m {e}\033[0m")
            writer.close()
            return

        if port == b"443":
            await self.fragment_data(reader, remote_writer)

        self.tasks.extend(
            [
                asyncio.create_task(
                    self.pipe(reader, remote_writer, 'out')),
                asyncio.create_task(
                    self.pipe(remote_reader, writer, 'in')),
            ]
        )

    async def pipe(self, reader, writer, direction):
        """
        Pipe data from a reader to a writer.

        This function reads data from a reader and writes it to a writer until
        the reader is closed or the writer is closed. If an error occurs during
        the transfer, the error is logged and the writer is closed.

        Parameters:
            reader (asyncio.StreamReader): The reader to read from
            writer (asyncio.StreamWriter): The writer to write to
            verbose (bool): Whether to print non-critical errors
        """
        try:
            while not reader.at_eof() and not writer.is_closing():
                data = await reader.read(1500)
                if direction == 'out':
                    self.traffic_out += len(data)
                else:
                    self.traffic_in += len(data)
                writer.write(data)
                await writer.drain()
        except Exception as e:
            logging.error(e)
            if self.verbose:
                print(f"\033[93m[NON-CRITICAL]:\033[97m {e}\033[0m")
        finally:
            writer.close()

    async def fragment_data(self, reader, writer):
        """
        Fragment data from a reader and write it to a writer.

        This function reads data from a reader and fragments it according to the
        blocked sites list. If the data does not contain any blocked sites, it is
        written to the writer as is. Otherwise, it is split into chunks and each
        chunk is written to the writer as a separate TLS record.

        Parameters:
            reader (asyncio.StreamReader): The reader to read from
            writer (asyncio.StreamWriter): The writer to write to
        """
        try:
            head = await reader.read(5)
            data = await reader.read(2048)
        except Exception as e:
            logging.error(e)
            if self.verbose:
                print(f"\033[93m[NON-CRITICAL]:\033[97m {e}\033[0m")
            return

        if all(site not in data for site in self.blocked):
            self.allowed_connections += 1
            writer.write(head + data)
            await writer.drain()
            return

        self.blocked_connections += 1

        parts = []
        host_end = data.find(b"\x00")
        if host_end != -1:
            parts.append(
                bytes.fromhex("1603")
                + bytes([random.randint(0, 255)])
                + (host_end + 1).to_bytes(2, "big")
                + data[: host_end + 1]
            )
            data = data[host_end + 1:]

        while data:
            chunk_len = random.randint(1, len(data))
            parts.append(
                bytes.fromhex("1603")
                + bytes([random.randint(0, 255)])
                + chunk_len.to_bytes(2, "big")
                + data[:chunk_len]
            )
            data = data[chunk_len:]

        writer.write(b"".join(parts))
        await writer.drain()

    async def shutdown(self):
        """
        Shutdown the proxy server.

        This function closes the server and cancels all tasks running on the
        event loop. If a server is not running, the function does nothing.
        """
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        for task in self.tasks:
            task.cancel()


class ProxyApplication:
    @staticmethod
    def parse_args():
        parser = argparse.ArgumentParser()
        parser.add_argument("--host", default="127.0.0.1", help="Proxy host")
        parser.add_argument("--port", type=int,
                            default=8881, help="Proxy port")
        parser.add_argument(
            "--blacklist", default="blacklist.txt", help="Path to blacklist file"
        )
        parser.add_argument("--log", default="errors.log",
                            help="Path to log file")
        parser.add_argument('-v', '--verbose', action='store_true',
                            help='Show more info')
        return parser.parse_args()

    @classmethod
    async def run(cls):
        args = cls.parse_args()
        proxy = ProxyServer(args.host, args.port,
                            args.blacklist, args.log, args.verbose)

        try:
            await proxy.run()
        except asyncio.CancelledError:
            await proxy.shutdown()
            print("\n\n\033[92m[INFO]:\033[97m Shutting down proxy...")
            try:
                sys.exit(0)
            except asyncio.CancelledError:
                pass


if __name__ == "__main__":
    try:
        asyncio.run(ProxyApplication.run())
    except KeyboardInterrupt:
        pass
