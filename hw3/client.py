import socket
import Tkinter as tk
import threading
from packet_struct import *
from msglib import *

root = None
sending_list = []
sending_list_lock = threading.Lock()

# Join to a group
def add_new_grp():

    grp_ip = "224.29.3.1"  # raw_input("Give grp chat IP: ")
    grp_port = int(raw_input("Give grp port: "))
    nickname = "takis"  # raw_input("Give nickname: ")

    return grp_join(grp_ip, grp_port, nickname)


def Enter_pressed(event, input_user):

    input_get = input_user.get()
    input_user.delete(0, "end")

    # import on sending_msg
    sending_list_lock.acquire()
    sending_list.append(input_user)
    sending_list_lock.release()


def create_window_chat():

    global root

    new_window = tk.Toplevel(root)
    new_window.title("Chat")

    # Text Widget
    output_widget = tk.Text(new_window)
    output_widget.pack()

    # Entry Widget
    input_user = tk.StringVar()
    input_widget = tk.Entry(new_window, text=input_user)
    input_widget.bind("<Return>", lambda event: Enter_pressed(event, input_widget))
    input_widget.pack(side=tk.BOTTOM, fill=tk.BOTH)

    return (input_widget, output_widget)

def chat_worker(gsocket):

    input_widget, output_widget = create_window_chat()

def main_thread():

    while (1):

        join_or_leave = int(raw_input("Join or leave a group (0/1): "))

        if (join_or_leave == 0):
            gsocket = add_new_grp()
            t = threading.Thread(target=chat_worker, args=(gsocket,))
            t.start()


def main():
    
    global root

    service_ip = raw_input("Give service IP: ")
    service_port = int(raw_input("Give service port: "))

    # set Directory service address!
    grp_setDir(service_ip, service_port)

    root = tk.Tk()
    root.withdraw()

    # start main thread
    t = threading.Thread(target=main_thread)
    t.start()
    root.mainloop()

if __name__ == "__main__" :
    main()
