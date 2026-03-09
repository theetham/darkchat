# นำเข้าไลบรารีที่จำเป็น
import socket          # ใช้สำหรับเชื่อมต่อเครือข่าย
import threading       # ใช้สร้าง thread เพื่อรับข้อความพร้อมกับ GUI
import json            # ใช้แปลงข้อมูล JSON จาก server
import tkinter as tk   # ใช้สร้าง GUI
from tkinter import simpledialog, messagebox
import hashlib         # ใช้สร้าง hash เพื่อกำหนดสีของผู้ใช้

# กำหนด IP และ port ของ server
host = "10.34.9.209"
port = 5000

# สร้าง socket client และเชื่อมต่อไปยัง server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((host, port))

# สร้างหน้าต่าง tkinter หลัก
root = tk.Tk()
root.withdraw()  # ซ่อนหน้าต่างก่อนเพื่อถาม username


# ฟังก์ชันถาม username จากผู้ใช้
def check_username():
    while True:
        username = simpledialog.askstring("Username", "Enter username", parent=root)
        # ตรวจสอบว่า username ไม่ว่าง
        if username and not username.isspace():
            return username
        else:
            messagebox.showwarning("Invalid Username", "Username cannot be empty")


# รับ username
username = check_username()

# แสดงหน้าต่างหลัก
root.deiconify()
root.title(f"Python Chat - {username}")
root.geometry("700x550")
root.configure(bg="#2f3136")

# dictionary เก็บสีของ user แต่ละคน
user_colors = {}

# รายการ emoji ที่ใช้ในโปรแกรม
emoji_list = ["😀","😂","😍","😎","😭","👍","🔥","❤️","🎉","😆"]


# ฟังก์ชันสร้างสีจากชื่อผู้ใช้
def get_color(name):
    h = hashlib.md5(name.encode()).hexdigest()
    return "#" + h[:6]


# เพิ่ม emoji ลงในช่องพิมพ์ข้อความ
def add_emoji(e):
    msg_entry.insert(tk.END, e)


# ---------------------------
# ส่วน Layout GUI
# ---------------------------

# frame ด้านซ้าย (แสดงรายชื่อผู้ใช้)
left = tk.Frame(root, bg="#36393f", width=200)
left.pack(side=tk.LEFT, fill=tk.Y)

# frame ด้านขวา (แชท)
right = tk.Frame(root, bg="#2f3136")
right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# label ONLINE
tk.Label(left, text="ONLINE", bg="#36393f", fg="white").pack(pady=10)

# listbox แสดงรายชื่อผู้ใช้
user_list = tk.Listbox(left, bg="#2f3136", fg="white", font=("Arial", 12))
user_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# frame สำหรับกล่องแชท
chat_frame = tk.Frame(right, bg="#2f3136")
chat_frame.pack(fill=tk.BOTH, expand=True)

# scrollbar ของกล่องแชท
scroll = tk.Scrollbar(chat_frame)
scroll.pack(side=tk.RIGHT, fill=tk.Y)

# กล่องข้อความแชท
chat_box = tk.Text(chat_frame, bg="#2f3136", fg="white",
                   yscrollcommand=scroll.set, state="disabled",
                   wrap="word", font=("Arial", 12))
chat_box.pack(fill=tk.BOTH, expand=True)

scroll.config(command=chat_box.yview)

# ตั้งค่า tag จัดตำแหน่งข้อความ
chat_box.tag_config("left", justify="left")
chat_box.tag_config("right", justify="right")

# frame สำหรับช่องพิมพ์ข้อความ
input_frame = tk.Frame(right, bg="#40444b")
input_frame.pack(fill=tk.X)


# ---------------------------
# ฟังก์ชันควบคุมโปรแกรม
# ---------------------------

# ออกจากโปรแกรม
def exit_chat():
    try:
        client.close()
    except:
        pass
    root.destroy()


# ส่งข้อความไป server
def send_msg(event=None):
    msg = msg_entry.get()
    if msg:
        client.send(msg.encode())
        msg_entry.delete(0, tk.END)


# ปุ่ม Exit
exit_btn = tk.Button(input_frame, text="Exit", bg="#ed4245", fg="white", command=exit_chat)
exit_btn.pack(side=tk.LEFT, padx=10, pady=10)

# ปุ่ม emoji
emoji_btn = tk.Button(input_frame, text="😀", font=("Arial",14), command=lambda: open_emoji())
emoji_btn.pack(side=tk.LEFT, padx=5)

# ช่องพิมพ์ข้อความ
msg_entry = tk.Entry(input_frame, bg="#40444b", fg="white", insertbackground="white")
msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=10)

# ปุ่ม Send
send_btn = tk.Button(input_frame, text="Send", bg="#5865f2", fg="white", command=send_msg)
send_btn.pack(side=tk.RIGHT, padx=10, pady=10)

# กด Enter เพื่อส่งข้อความ
msg_entry.bind("<Return>", send_msg)


# ---------------------------
# ฟังก์ชันแสดงข้อความในแชท
# ---------------------------

def add_chat(text, uid=None):
    chat_box.config(state="normal")

    # ถ้ามีชื่อผู้ส่ง (รูปแบบ name: message)
    if ":" in text:
        name, message = text.split(":", 1)

        # สลับข้อความให้เหมือน bubble chat
        text = f"{message.strip()}: {name.strip()}"

        key = uid if uid else name

        # กำหนดสี user ถ้ายังไม่มี
        if key not in user_colors:
            color = get_color(key)
            user_colors[key] = color
            chat_box.tag_config(key, foreground=color)

        # ถ้าเป็นข้อความของเรา -> ชิดขวา
        tag = ("right", key) if name == username else ("left", key)

        chat_box.insert(tk.END, text + "\n", tag)

    else:
        chat_box.insert(tk.END, text + "\n")

    chat_box.config(state="disabled")
    chat_box.yview(tk.END)


# ---------------------------
# อัปเดตรายชื่อผู้ใช้
# ---------------------------

def update_users(users):
    user_list.delete(0, tk.END)

    for user in users:
        name = user["name"]
        uid = user["uid"]

        user_list.insert(tk.END, name)

        index = user_list.size() - 1
        color = get_color(uid)

        # กำหนดสี username
        user_list.itemconfig(index, fg=color)


# ---------------------------
# รับข้อมูลจาก server
# ---------------------------

def receive():
    buffer = ""

    while True:
        try:
            data = client.recv(1024).decode()

            if not data:
                buffer = ""
                root.after(0, reset_ui)
                break

            buffer += data

            # แยกข้อความตาม newline
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)

                # server ขอชื่อ
                if line == "NAME":
                    client.send(username.encode())
                    continue

                packet = json.loads(line)

                # ข้อความแชท
                if packet["type"] == "chat":
                    add_chat(packet["data"], packet.get("uid"))

                # ข้อความระบบ
                elif packet["type"] == "system":
                    add_chat("[SYSTEM] " + packet["data"])

                # รายชื่อผู้ใช้
                elif packet["type"] == "users":
                    update_users(packet["data"])

                # ประวัติแชท
                elif packet["type"] == "history":
                    for m in packet["data"]:
                        add_chat(m["text"], m.get("uid"))

        except:
            root.after(0, reset_ui)
            break


# รีเซ็ต UI ถ้า server ปิด
def reset_ui():
    chat_box.config(state="normal")
    chat_box.delete("1.0", tk.END)
    chat_box.config(state="disabled")

    user_list.delete(0, tk.END)
    user_colors.clear()

    add_chat("[SYSTEM] Server ปิดแล้ว")


# ---------------------------
# หน้าต่างเลือก emoji
# ---------------------------

def open_emoji():
    win = tk.Toplevel(root)
    win.title("Emoji")
    win.configure(bg="#2f3136")

    row = 0
    col = 0

    for e in emoji_list:
        btn = tk.Button(
            win,
            text=e,
            font=("Arial",18),
            width=3,
            command=lambda emoji=e: (add_emoji(emoji), win.destroy())
        )

        btn.grid(row=row, column=col, padx=5, pady=5)

        col += 1
        if col == 5:
            col = 0
            row += 1


# ---------------------------
# สร้าง thread รับข้อความ
# ---------------------------

thread = threading.Thread(target=receive, daemon=True)
thread.start()

# เมื่อกดปิดหน้าต่าง
root.protocol("WM_DELETE_WINDOW", exit_chat)

# เริ่ม GUI
root.mainloop()