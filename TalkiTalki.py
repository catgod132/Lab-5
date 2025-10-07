from machine import UART, Pin
import time
import _thread

# --- CONFIG ---
UART_ID = 1
TX_PIN = 8
RX_PIN = 9
BAUD = 9600
KEEPALIVE_INTERVAL = 10
# --------------

try:
    uart = UART(UART_ID, baudrate=BAUD, tx=Pin(TX_PIN), rx=Pin(RX_PIN))
    uart.init(bits=8, parity=None, stop=1)
except Exception as e:
    print("UART init error:", e)
    raise SystemExit

send_queue = []
queue_lock = _thread.allocate_lock()
last_send_time = time.time()

print("UART Chat Ready. Type and press Enter to send.\n")

def input_thread():
    while True:
        try:
            line = input()
            if line:
                queue_lock.acquire()
                send_queue.append(line.strip())
                queue_lock.release()
        except Exception as e:
            print("Input error:", e)
            time.sleep(1)

def format_timestamp(t):
    t = int(t)
    h, m, s = (t // 3600) % 24, (t // 60) % 60, t % 60
    return "{:02d}:{:02d}:{:02d}".format(h, m, s)

try:
    _thread.start_new_thread(input_thread, ())
except Exception as e:
    print("Thread start failed:", e)
    raise SystemExit

try:
    while True:
        # Receive
        try:
            if uart.any():
                data = uart.readline()
                if data:
                    try:
                        text = data.decode().strip()
                    except Exception:
                        text = str(data)
                    print("[Partner]:", text)
        except Exception as e:
            print("UART read error:", e)

        # Send
        msg = None
        queue_lock.acquire()
        if send_queue:
            msg = send_queue.pop(0)
        queue_lock.release()

        if msg:
            try:
                uart.write(msg + "\n")
                print("[You]:", msg)
                last_send_time = time.time()
            except Exception as e:
                print("UART send error:", e)

        # Keep-alive
        now = time.time()
        if now - last_send_time >= KEEPALIVE_INTERVAL:
            try:
                msg = "Keep-alive: " + format_timestamp(now)
                uart.write(msg + "\n")
                print("[KeepAlive]:", msg)
                last_send_time = now
            except Exception as e:
                print("Keep-alive send error:", e)

        time.sleep(0.03)

except KeyboardInterrupt:
    print("Chat stopped.")
except Exception as e:
    print("Fatal error:", e)
finally:
    uart.deinit()
    print("UART closed.")
