import threading

def say_hello():
    print("Hello from thread!")

t = threading.Thread(target=say_hello)
t.start()
t.join()
print("Back in main thread.")
