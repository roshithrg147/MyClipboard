#!/usr/bin/env python3
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                Author: RR                                     #
#                                Software Architect                             #
#                                Pilatewaveai                                   #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
import sys
import socket
import argparse

SOCKET_PATH = "/tmp/myclipboard.sock"

def send_to_daemon(data: str):
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(SOCKET_PATH)
        # Send data with the ADD: prefix
        client.sendall(f"ADD:{data}".encode('utf-8'))
        client.close()
    except FileNotFoundError:
        print("Error: MyClipboard daemon is not running. Socket file not found.", file=sys.stderr)
        sys.exit(1)
    except ConnectionRefusedError:
        print("Error: MyClipboard daemon socket exists but connection was refused.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error communicating with MyClipboard daemon: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="MyClipboard CLI Utility (mcb). Pipe data directly into your clipboard history."
    )
    parser.add_argument("text", nargs="*", help="Text to copy (if not piping)")
    args = parser.parse_args()

    # Check if data is piped into stdin
    if not sys.stdin.isatty():
        piped_data = sys.stdin.read()
        if piped_data:
            send_to_daemon(piped_data)
    else:
        # If running interactively, check for positional args
        if args.text:
            text_data = " ".join(args.text)
            send_to_daemon(text_data)
        else:
            parser.print_help()
            print("\nExamples:")
            print("  cat mylog.txt | mcb")
            print("  mcb \"This is a direct string\"")

if __name__ == "__main__":
    main()
