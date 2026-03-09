import socket
import threading
import json
import tkinter as tk
from tkinter import messagebox
import hashlib

client = None
username = ""

# emoji
emoji_list = ["😀","😂","😍","😎","😭","👍","🔥","❤️","🎉","😆"]

user_colors = {}


# ---------------------------
# ฟังก์ชันสร้างสี
# ---------------------------
def get_color(name):
    h = hashlib.md5(name.encode()).hexdigest()
    return "#" + h[:6]


# ---------------------------
# หน้า LOGIN
# ---------------------------
login = tk.Tk()
login.title("Python Chat Login")
login.geometry("350x250")
login.configure(bg="#2f3136")

tk.Label(login,text="Python Chat",font=("Arial",20,"bold"),
         bg="#2f3136",fg="white").pack(pady=10)

tk.Label(login,text="Username",bg="#2f3136",fg="white").pack()
username_entry = tk.Entry(login)
username_entry.pack(pady=5)

tk.Label(login,text="Server IP",bg="#2f3136",fg="white").pack()
ip_entry = tk.Entry(login)
ip_entry.pack(pady=5)

tk.Label(login,text="Port",bg="#2f3136",fg="white").pack()
port_entry = tk.Entry(login)
port_entry.insert(0,"5000")
port_entry.pack(pady=5)


# ---------------------------
# เปิดหน้า CHAT
# ---------------------------
def start_chat():

    global client, username

    username = username_entry.get()
    host = ip_entry.get()
    port = port_entry.get()

    if username == "" or host == "" or port == "":
        messagebox.showwarning("Error","Please fill all fields")
        return

    try:
        port = int(port)
        client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        client.connect((host,port))
    except:
        messagebox.showerror("Error","Cannot connect to server")
        return

    login.destroy()
    open_chat()


# ---------------------------
# GUI CHAT
# ---------------------------
def open_chat():

    root = tk.Tk()
    root.title(f"Python Chat - {username}")
    root.geometry("700x550")
    root.configure(bg="#2f3136")

    # frame ซ้าย
    left = tk.Frame(root,bg="#36393f",width=200)
    left.pack(side=tk.LEFT,fill=tk.Y)

    # frame ขวา
    right = tk.Frame(root,bg="#2f3136")
    right.pack(side=tk.RIGHT,fill=tk.BOTH,expand=True)

    tk.Label(left,text="ONLINE",bg="#36393f",fg="white").pack(pady=10)

    user_list = tk.Listbox(left,bg="#2f3136",fg="white",font=("Arial",12))
    user_list.pack(fill=tk.BOTH,expand=True,padx=5,pady=5)

    # chat frame
    chat_frame = tk.Frame(right,bg="#2f3136")
    chat_frame.pack(fill=tk.BOTH,expand=True)

    scroll = tk.Scrollbar(chat_frame)
    scroll.pack(side=tk.RIGHT,fill=tk.Y)

    chat_box = tk.Text(chat_frame,bg="#2f3136",fg="white",
                       yscrollcommand=scroll.set,
                       state="disabled",
                       wrap="word",
                       font=("Arial",12))

    chat_box.pack(fill=tk.BOTH,expand=True)
    scroll.config(command=chat_box.yview)

    chat_box.tag_config("left",justify="left")
    chat_box.tag_config("right",justify="right")

    input_frame = tk.Frame(right,bg="#40444b")
    input_frame.pack(fill=tk.X)

    # ---------------------------
    # ฟังก์ชัน
    # ---------------------------

    def exit_chat():
        try:
            client.close()
        except:
            pass
        root.destroy()

    def send_msg(event=None):

        msg = msg_entry.get()

        if msg:
            client.send(msg.encode())
            msg_entry.delete(0,tk.END)

    def add_chat(text,uid=None):

        chat_box.config(state="normal")

        if ":" in text:

            name,message = text.split(":",1)

            text = f"{message.strip()}: {name.strip()}"

            key = uid if uid else name

            if key not in user_colors:
                color = get_color(key)
                user_colors[key] = color
                chat_box.tag_config(key,foreground=color)

            tag = ("right",key) if name == username else ("left",key)

            chat_box.insert(tk.END,text+"\n",tag)

        else:
            chat_box.insert(tk.END,text+"\n")

        chat_box.config(state="disabled")
        chat_box.yview(tk.END)

    def update_users(users):

        user_list.delete(0,tk.END)

        for user in users:

            name = user["name"]
            uid = user["uid"]

            user_list.insert(tk.END,name)

            index = user_list.size()-1

            color = get_color(uid)

            user_list.itemconfig(index,fg=color)

    def reset_ui():

        chat_box.config(state="normal")
        chat_box.delete("1.0",tk.END)
        chat_box.config(state="disabled")

        user_list.delete(0,tk.END)
        user_colors.clear()

        add_chat("[SYSTEM] Server ปิดแล้ว")

    # ---------------------------
    # emoji window
    # ---------------------------

    def add_emoji(e):
        msg_entry.insert(tk.END,e)

    def open_emoji():

        win = tk.Toplevel(root)
        win.title("Emoji")

        row = 0
        col = 0

        for e in emoji_list:

            btn = tk.Button(
                win,
                text=e,
                font=("Arial",18),
                width=3,
                command=lambda emoji=e:(add_emoji(emoji),win.destroy())
            )

            btn.grid(row=row,column=col,padx=5,pady=5)

            col+=1

            if col==5:
                col=0
                row+=1

    # ---------------------------
    # receive thread
    # ---------------------------

    def receive():

        buffer=""

        while True:

            try:

                data = client.recv(1024).decode()

                if not data:
                    root.after(0,reset_ui)
                    break

                buffer+=data

                while "\n" in buffer:

                    line,buffer = buffer.split("\n",1)

                    if line == "NAME":
                        client.send(username.encode())
                        continue

                    packet = json.loads(line)

                    if packet["type"] == "chat":
                        add_chat(packet["data"],packet.get("uid"))

                    elif packet["type"] == "system":
                        add_chat("[SYSTEM] "+packet["data"])

                    elif packet["type"] == "users":
                        update_users(packet["data"])

                    elif packet["type"] == "history":
                        for m in packet["data"]:
                            add_chat(m["text"],m.get("uid"))

            except:
                root.after(0,reset_ui)
                break

    # ---------------------------
    # ปุ่ม
    # ---------------------------

    exit_btn = tk.Button(input_frame,text="Exit",bg="#ed4245",fg="white",command=exit_chat)
    exit_btn.pack(side=tk.LEFT,padx=10,pady=10)

    emoji_btn = tk.Button(input_frame,text="😀",font=("Arial",14),command=open_emoji)
    emoji_btn.pack(side=tk.LEFT,padx=5)

    msg_entry = tk.Entry(input_frame,bg="#40444b",fg="white",insertbackground="white")
    msg_entry.pack(side=tk.LEFT,fill=tk.X,expand=True,padx=5,pady=10)

    send_btn = tk.Button(input_frame,text="Send",bg="#5865f2",fg="white",command=send_msg)
    send_btn.pack(side=tk.RIGHT,padx=10,pady=10)

    msg_entry.bind("<Return>",send_msg)

    thread = threading.Thread(target=receive,daemon=True)
    thread.start()

    root.protocol("WM_DELETE_WINDOW",exit_chat)

    root.mainloop()


# ---------------------------
# ปุ่ม Connect
# ---------------------------

connect_btn = tk.Button(login,text="Connect",
                        bg="#5865f2",
                        fg="white",
                        width=15,
                        command=start_chat)

connect_btn.pack(pady=15)

login.mainloop()