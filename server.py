import socket
import threading
import json
import customtkinter as ctk

# ตั้งค่า theme ของ GUI เป็น dark mode และธีมสีหลักเป็น blue
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# สร้างหน้าต่างหลักของโปรแกรม
app = ctk.CTk()
app.title("Server")  
app.geometry("300x150")  

# สร้าง label สำหรับแสดงสถานะของ server
status_label = ctk.CTkLabel(
    app,
    text="สถานะ: ปิดเซิร์ฟเวอร์อยู่",  
    font=("Arial", 18),
    text_color="red" 
)
status_label.pack(pady=10)

# กำหนด IP และ port ของ server
host = "10.160.63.100"
port = 5000

# dictionary เก็บ client ที่เชื่อมต่อ {conn: uid}
clients = {}

# lock สำหรับ thread safety
lock = threading.Lock()

# เก็บประวัติข้อความ chat
history = []

# ตัวแปรสำหรับ socket server และสถานะ server
server = None
server_running = False

# ตัวนับ UID ของ user
user_counter = 1


# ฟังก์ชัน log ข้อความทั้ง console และ GUI
def log(msg):
    print(msg)
    status_label.configure(text=msg)


# ส่งข้อความไปยัง client ทุกคน
def broadcast(msg):
    for c in list(clients.keys()):
        try:
            c.send((msg + "\n").encode())
        except:  # ถ้า client หลุด ไม่ให้ server crash
            pass


# ส่งรายชื่อผู้ใช้งานทุกคนไปยัง client
def send_user_list():
    users = []
    for uid in clients.values():
        name = uid.split("#")[0]  
        users.append({"name": name, "uid": uid})

    packet = json.dumps({
        "type": "users",
        "data": users
    })
    broadcast(packet)  # ส่งให้ทุกคน


# ฟังก์ชันจัดการ client แต่ละคน
def handle_client(conn):
    uid = clients[conn]  # ดึง uid ของ client
    name = uid.split("#")[0]  # แยกชื่อ

    while server_running:  # วน loop จน server ปิด
        try:
            msg = conn.recv(1024).decode()  # รับข้อความ
            if not msg:
                break  # ถ้าไม่มีข้อความ แสดงว่า client หลุด

            text = f"{name}: {msg}"  # เพิ่มชื่อผู้ส่ง

            # เก็บข้อความลง history
            history.append({
                "text": text,
                "uid": uid
            })

            # แปลงข้อความเป็น JSON format และส่งให้ทุกคน
            packet = json.dumps({
                "type": "chat",
                "data": text,
                "uid": uid
            })
            broadcast(packet)

        except:
            break  # หากเกิดข้อผิดพลาด ให้ออกจาก loop

    # ลบ client ออกจาก dictionary ป้องกันการแข่งกันเขียน
    with lock:
        if conn in clients:
            del clients[conn]

    # แจ้ง client อื่น ๆ ว่ามีคนออก
    broadcast(json.dumps({
        "type": "system",
        "data": f"{name} left the chat"
    }))

    # ส่งรายชื่อผู้ใช้ที่อัปเดตแล้ว
    send_user_list()
    conn.close()  # ปิดการเชื่อมต่อ


# ฟังก์ชันหลักของ server
def server_loop():
    global server, user_counter
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # สร้าง TCP socket
    server.bind((host, port))  # bind IP และ port
    server.listen()  # เริ่มฟังการเชื่อมต่อ
    log("สถานะ: เซิร์ฟเวอร์กำลังทำงาน")

    while server_running:
        try:
            conn, addr = server.accept()  # รอ client เชื่อมต่อ

            conn.send("NAME\n".encode())  # ขอชื่อ client
            name = conn.recv(1024).decode().strip()  # รับชื่อ client

            uid = f"{name}#{user_counter}"  # สร้าง UID
            user_counter += 1  # เพิ่ม counter

            # เก็บ client ลง dictionary
            with lock:
                clients[conn] = uid

            # ส่ง chat history ให้ client ใหม่
            packet = json.dumps({
                "type": "history",
                "data": history
            })
            conn.send((packet + "\n").encode())

            # แจ้งผู้ใช้อื่น ๆ ว่ามีคนเข้ามา
            broadcast(json.dumps({
                "type": "system",
                "data": f"{name} joined the chat"
            }))
            send_user_list()  # ส่ง list user อัปเดต

            # สร้าง thread แยกสำหรับ client นี้
            thread = threading.Thread(
                target=handle_client,
                args=(conn,),
                daemon=True
            )
            thread.start()

        except:
            break  # หากเกิดข้อผิดพลาด ให้หยุด loop


# ฟังก์ชันเริ่ม server
def start_server():
    global server_running
    if server_running:
        return  # ถ้า server กำลังทำงานอยู่แล้ว ไม่ทำอะไร

    server_running = True
    threading.Thread(target=server_loop, daemon=True).start()  # สร้าง thread server
    status_label.configure(
        text="สถานะ: Server กำลังทำงานอยู่",
        text_color="lightgreen"
    )


# ฟังก์ชันหยุด server
def stop_server():
    global server_running, server, history
    server_running = False
    if server:
        server.close()  # ปิด socket server
    history.clear()  # ล้าง chat history
    status_label.configure(
        text="สถานะ: ปิดเซิร์ฟเวอร์แล้ว",
        text_color="red"
    )


# สร้างปุ่ม GUI สำหรับ start/stop server
start_button = ctk.CTkButton(app, text="Start Server", command=start_server)
start_button.pack(pady=10)

stop_button = ctk.CTkButton(app, text="Stop Server", fg_color="red", command=stop_server)
stop_button.pack(pady=10)

# รัน GUI
app.mainloop()