import socket
import time
import Tkinter as tk
import threading
from packet_struct import *
from msglib import *

# MESSAGE TYPES
MESSAGE = 0
ANOTHER_MEMBER_DISCONNECTED = -1
I_DISCONNECTED = -2
SOMEONE_IS_CONNECTED = 1


root = None
sending_dict = {}
sending_dict_lock = threading.Lock()

# socket for every group
gsocket_to_group = {}

# variables for every gsocket
gsocket_variables = {}
gsocket_variables_lock = threading.Lock()


# Join to a group
def add_new_grp():

    grp_ip = "224.29.3.1"  # raw_input("Give grp chat IP: ")
    grp_port = int(raw_input("Give grp port: "))
    nickname = raw_input("Give nickname: ")

    return [grp_join(grp_ip, grp_port, nickname), grp_ip, grp_port, nickname]


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


def create_window_chat(grp_ipaddr, grp_port, name):

    global root

    new_window = tk.Toplevel(root)
    new_window.title("(ip: " + str(grp_ipaddr) + "), (port: " + str(grp_port) + "), (name: " + str(name) + ")")

    # Text Widget
    output_widget = tk.Text(new_window)
    output_widget.pack()

    # Entry Widget
    input_user = tk.StringVar()
    input_widget = tk.Entry(new_window, text=input_user)
    input_widget.bind("<Return>", lambda event: Enter_pressed(event, input_widget))
    input_widget.pack(side=tk.BOTTOM, fill=tk.BOTH)

    return (input_widget, output_widget, new_window)


def send_worker(gsocket, input_widget):

    global sending_dict

    # Send all messages!
    while(1):

        # check to stop sending at this group!
        gsocket_variables_lock.acquire()
        if (gsocket_variables[gsocket] is True):
            gsocket_variables_lock.release()
            print 'Sender done!'
            break
        gsocket_variables_lock.release()

        sending_dict_lock.acquire()
        if (input_widget in sending_dict.keys()):
            if (sending_dict[input_widget] is not []):
                for msg in sending_dict[input_widget]:
                    grp_send(gsocket, msg)

                sending_dict[input_widget] = []
        sending_dict_lock.release()


def receive_worker(gsocket, output_widget, window_object):

    while(1):

        msg, msg_type = grp_recv(gsocket)
        output_widget.insert(tk.END, msg + "\n")

        # edw tha allaxi to ti mnm epistrefi! Einai mnm h bgainw apo group chat!
        if ('disconnected' in msg.split()):
            time.sleep(2)
            window_object.destroy()
            print 'Receiver done'
            break


def chat_worker(gsocket, grp_ipaddr, grp_port, name):

    input_widget, output_widget, window_object = create_window_chat(grp_ipaddr, grp_port, name)

    t_worker = threading.Thread(target=send_worker, args=(gsocket, input_widget)).start()
    t_receiver = threading.Thread(target=receive_worker, args=(gsocket, output_widget, window_object)).start()


def main_thread():

    while (1):

        join_or_leave = int(raw_input("Join or leave a group (0/1): "))

        if (join_or_leave == 0):
            gsocket, grp_ipaddr, grp_port, name = add_new_grp()

            # update dictionaries
            gsocket_to_group[(grp_ipaddr, grp_port)] = gsocket

            gsocket_variables_lock.acquire()
            gsocket_variables[gsocket] = False
            gsocket_variables_lock.release()

            t = threading.Thread(target=chat_worker, args=(gsocket, grp_ipaddr, grp_port, name))
            t.start()
        else:

            group_exit_ipaddr = raw_input("Give group ipaddr: ")
            group_exit_port = int(raw_input("Give group port: "))
            if ((group_exit_ipaddr, group_exit_port) in gsocket_to_group.keys()):

                # notify send worker to terminate
                gsocket_variables_lock.acquire()
                gsocket_variables[gsocket] = True
                gsocket_variables_lock.release()

                gsocket = gsocket_to_group[(group_exit_ipaddr, group_exit_port)]
                grp_leave(gsocket)
            else:
                print "Unknown group. Please try again!"


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
