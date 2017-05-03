import socket
import Tkinter as tk
import threading
from packet_struct import *
from msglib import *

root = None
sending_dict = {}
sending_dict_lock = threading.Lock()

# Join to a group
def add_new_grp():

    grp_ip = "224.29.3.1"  # raw_input("Give grp chat IP: ")
    grp_port = int(raw_input("Give grp port: "))
    nickname = raw_input("Give nickname: ")

    return grp_join(grp_ip, grp_port, nickname)


def Enter_pressed(event, input_widget):

    input_get = input_widget.get()
    input_widget.delete(0, "end")

    # import on sending_msg
    sending_dict_lock.acquire()
    if (input_widget in sending_dict.keys()):
        sending_dict[input_widget].append(input_get)
    else:
        sending_dict[input_widget] = [input_get]
    sending_dict_lock.release()


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

def send_worker(gsocket, input_widget):

    global sending_dict

    # Send all messages!
    while(1):
        sending_dict_lock.acquire()
        if (input_widget in sending_dict.keys()):
            if (sending_dict[input_widget] is not []):
                for msg in sending_dict[input_widget]:
                    grp_send(gsocket, msg)

                sending_dict[input_widget] = []
        sending_dict_lock.release()

def receive_worker(gsocket, output_widget):

    while(1):

        msg = grp_recv(gsocket)
        output_widget.insert(tk.END, msg)

def chat_worker(gsocket):

    input_widget, output_widget = create_window_chat()

    t_worker = threading.Thread(target=send_worker, args=(gsocket, input_widget)).start()
    t_receiver = threading.Thread(target=receive_worker, args=(gsocket, output_widget)).start()

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
