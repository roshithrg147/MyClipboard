# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                Author: RR                                     #
#                                Software Architect                             #
#                                Pilatewaveai                                   #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

import sys
import socket

SOCKET_PATH = "/tmp/myclipboard.sock"

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("MyClipboard CLI (mcb)")
            print("Usage:")
            print("  echo 'text' | mcb      - Add text to clipboard history")
            print("  mcb show               - Show history window")
            sys.exit(0)
            
        if sys.argv[1] == "show":
            msg = "SHOW"
        else:
            msg = f"ADD:{' '.join(sys.argv[1:])}"
    else:
        # Check if stdin has content
        if not sys.stdin.isatty():
            msg = f"ADD:{sys.stdin.read().strip()}"
        else:
            msg = "SHOW"

    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(SOCKET_PATH)
        client.sendall(msg.encode('utf-8'))
        client.close()
    except Exception as e:
        print(f"Error: Could not connect to MyClipboard daemon. Is it running? ({e})")
        sys.exit(1)

if __name__ == "__main__":
    main()
