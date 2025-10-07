from machine import UART, Pin
import time

# --- CONFIG ---
UART_ID = 1
TX_PIN = 8
RX_PIN = 9
BAUD = 9600
KEEPALIVE_INTERVAL = 10      # send keep-alive every 10s
SESSION_TIMEOUT = 30         # stop 30s after program starts
# ----------------

# UART setup
try:
    uart = UART(UART_ID, baudrate=BAUD, tx=Pin(TX_PIN), rx=Pin(RX_PIN))
    uart.init(bits=8, parity=None, stop=1)
except Exception as e:
    print("UART init error:", e)
    raise SystemExit

start_time = time.time()
last_send_time = start_time

print("UART Chat Ready. Program will close after 30 seconds.\n")

# hh:mm:ss formatter
def format_timestamp(t):
    t = int(t)
    h, m, s = (t // 3600) % 24, (t // 60) % 60, t % 60
    return "{:02d}:{:02d}:{:02d}".format(h, m, s)

try:
    while True:
        now = time.time()

        # --- Check for incoming messages ---
        if uart.any():
            data = uart.readline()
            if data:
                try:
                    text = data.decode().strip()
                except Exception:
                    text = str(data)
                print("[Partner]:", text)

        # --- Send keep-alive if idle ---
        if now - last_send_time >= KEEPALIVE_INTERVAL:
            try:
                msg = "Keep-alive: " + format_timestamp(now)
                uart.write(msg + "\n")
                print("[KeepAlive]:", msg)
                last_send_time = now
            except Exception as e:
                print("Keep-alive send error:", e)

        # User input
        if now % 2 < 0.25:  # prompt roughly every 2 seconds
            try:
                msg = input("You: ").strip()
                if msg:
                    uart.write(msg + "\n")
                    print("[Sent]:", msg)
                    last_send_time = now
            except Exception as e:
                print("Input or send error:", e)

        # session timeout 
        if now - start_time >= SESSION_TIMEOUT:
            print("\n[INFO] 30 seconds elapsed. Closing chat.")
            break

        time.sleep(0.25)

# cleanup ports
except KeyboardInterrupt:
    print("Chat stopped by user.")
except Exception as e:
    print("Fatal error:", e)
finally:
    uart.deinit()
    print("UART closed.")
