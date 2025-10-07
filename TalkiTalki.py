# UART chat for two Pico boards (MicroPython)
# Works in VS Code terminals. Uses _thread so incoming messages are printed
# while you type (input() runs in background thread).

from machine import UART, Pin
import time
import _thread

# ----- CONFIG -----
UART_ID = 1
TX_PIN = 8   # GP8
RX_PIN = 9   # GP9
BAUD = 9600
KEEPALIVE_INTERVAL = 10  # seconds between keep-alives when idle
# ------------------

uart = UART(UART_ID, baudrate=BAUD, tx=Pin(TX_PIN), rx=Pin(RX_PIN))
uart.init(bits=8, parity=None, stop=1)

# Shared simple queue for outgoing messages
send_queue = []
queue_lock = _thread.allocate_lock()

last_send_time = time.time()

print("UART Chat (Pico). Type a message and press Enter to send.")
print("Keep-alive every", KEEPALIVE_INTERVAL, "s when idle.\n")

def input_thread():
    """Background thread: blocking input() to collect user messages."""
    while True:
        try:
            line = input()  # blocking; works in VS Code terminal
        except Exception:
            # If input fails for any reason, just try again
            continue
        if line is None:
            continue
        line = line.strip()
        if line:
            queue_lock.acquire()
            send_queue.append(line)
            queue_lock.release()
        # pressing Enter on empty line simply does nothing

# Start the background input thread
_thread.start_new_thread(input_thread, ())

def format_timestamp(t):
    """Simple hh:mm:ss from seconds since boot (no strftime)."""
    t = int(t)
    h = (t // 3600) % 24
    m = (t // 60) % 60
    s = t % 60
    return "{:02d}:{:02d}:{:02d}".format(h, m, s)

# Main loop: receive, send queued messages, and keepalive
try:
    while True:
        # 1) Receive incoming UART data continuously
        if uart.any():
            data = uart.readline()
            if data:
                try:
                    text = data.decode().rstrip('\r\n')
                except Exception:
                    text = repr(data)
                # Print partner message on its own line
                print("[Partner]:", text)

        # 2) If user typed something (in background thread), send it
        msg_to_send = None
        queue_lock.acquire()
        if send_queue:
            msg_to_send = send_queue.pop(0)
        queue_lock.release()

        if msg_to_send:
            uart.write(msg_to_send + "\n")
            print("[You]:", msg_to_send)
            last_send_time = time.time()
            # continue immediately to keep responsiveness

        # 3) Periodic keep-alive (simple timestamp, no strftime)
        now = time.time()
        if now - last_send_time >= KEEPALIVE_INTERVAL:
            stamp = format_timestamp(now)
            keep_msg = "Keep-alive: " + stamp
            uart.write(keep_msg + "\n")
            print("[You -> KeepAlive]:", keep_msg)
            last_send_time = now

        # small sleep to avoid busy-looping
        time.sleep(0.03)

except KeyboardInterrupt:
    print("Exiting chat.")
