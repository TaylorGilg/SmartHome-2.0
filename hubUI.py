from tkinter import Tk, Label, Entry, Button, Text, Scrollbar, Toplevel, END, messagebox
from threading import Thread
from hub import Hub
from data.config import *

class HubUI:
    def __init__(self, hub):
        self.hub = hub
        self.root = Tk()
        self.root.title("IoT Hub")

        self.setup_ui()

    def setup_ui(self):
        Label(self.root, text="Device ID:").grid(row=0, column=0, padx=5, pady=5)
        Label(self.root, text="Device IP:").grid(row=1, column=0, padx=5, pady=5)
        Label(self.root, text="Device Port:").grid(row=2, column=0, padx=5, pady=5)

        self.device_id_entry = Entry(self.root)
        self.device_ip_entry = Entry(self.root)
        self.device_port_entry = Entry(self.root)

        self.device_id_entry.grid(row=0, column=1, padx=5, pady=5)
        self.device_ip_entry.grid(row=1, column=1, padx=5, pady=5)
        self.device_port_entry.grid(row=2, column=1, padx=5, pady=5)

        self.add_device_button = Button(self.root, text="Add Device", command=self.add_device)
        self.send_button = Button(self.root, text="Send Message", command=self.open_send_message_popup)
        self.view_blockchain_button = Button(self.root, text="View Blockchain", command=self.view_blockchain)  # New button
        self.receive_text = Text(self.root, height=10, width=50)
        self.device_list_text = Text(self.root, height=5, width=50)
        self.receive_text.config(state="disabled")
        self.device_list_text.config(state="disabled")

        self.add_device_button.grid(row=3, column=0, columnspan=2, pady=10)
        self.send_button.grid(row=4, column=0, columnspan=2, pady=10)
        self.view_blockchain_button.grid(row=5, column=0, columnspan=2, pady=10)  # Added button to grid
        self.receive_text.grid(row=6, column=0, columnspan=2, pady=10)  # Moved down one row
        self.device_list_text.grid(row=7, column=0, columnspan=2, pady=10)  # Moved down one row

        scrollbar_receive = Scrollbar(self.root, command=self.receive_text.yview)
        scrollbar_device_list = Scrollbar(self.root, command=self.device_list_text.yview)

        scrollbar_receive.grid(row=6, column=2, sticky='nsew')  # Updated row number
        scrollbar_device_list.grid(row=7, column=2, sticky='nsew')  # Updated row number

        self.receive_text['yscrollcommand'] = scrollbar_receive.set
        self.device_list_text['yscrollcommand'] = scrollbar_device_list.set

        # Start a thread to continuously listen for messages
        receive_thread = Thread(target=self.receive_messages)
        receive_thread.daemon = True  # Added daemon=True to prevent hanging on exit
        receive_thread.start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def add_device(self):
        device_id = self.device_id_entry.get()
        device_ip = self.device_ip_entry.get()
        device_port = self.device_port_entry.get()

        if device_id and device_ip and device_port:
            self.hub.register_device(device_id, device_ip, device_port)
            messagebox.showinfo("Device Added", f"Device {device_id} added successfully.")
            self.update_device_list()
        else:
            messagebox.showerror("Error", "All fields must be filled.")

# Display blockchain data from hub.
    def view_blockchain(self):
        blockchain_window = Toplevel(self.root)
        blockchain_window.title("Blockchain View")
        blockchain_window.geometry("800x600")

        blockchain_text = Text(blockchain_window, wrap="word", height=30, width=90)
        scrollbar = Scrollbar(blockchain_window, command=blockchain_text.yview)
        blockchain_text.configure(yscrollcommand=scrollbar.set)

        blockchain_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Get blockchain data from hub's communicator
        blockchain_data = self.hub.get_blockchain_data()
        
        for block in blockchain_data:
            blockchain_text.insert(END, f"\nBlock {block['index']}:\n")
            blockchain_text.insert(END, f"Timestamp: {block['timestamp']}\n")
            blockchain_text.insert(END, f"Previous Hash: {block['previous_hash']}\n")
            blockchain_text.insert(END, "\nInteractions:\n")
            
            for interaction in block['interactions']:
                blockchain_text.insert(END, f"\nFrom: {interaction['sender']}\n")
                blockchain_text.insert(END, f"To: {interaction['recipient']}\n")
                blockchain_text.insert(END, f"Data: {interaction['data']}\n")
                blockchain_text.insert(END, "-" * 50 + "\n")

        blockchain_text.config(state="disabled")
    def open_send_message_popup(self):
        popup = Toplevel(self.root)
        popup.title("Send Message")

        Label(popup, text="Device ID:").grid(row=0, column=0, padx=5, pady=5)
        Label(popup, text="Message:").grid(row=1, column=0, padx=5, pady=5)

        device_id_entry = Entry(popup)
        message_entry = Entry(popup)

        device_id_entry.grid(row=0, column=1, padx=5, pady=5)
        message_entry.grid(row=1, column=1, padx=5, pady=5)

        send_button = Button(popup, text="Send", command=lambda: self.send_message_popup(device_id_entry.get(), message_entry.get(), popup))
        send_button.grid(row=2, column=0, columnspan=2, pady=10)

    def send_message_popup(self, device_id, message, popup):
        popup.destroy()  # Close the popup window

        if device_id and message:
            try:
                recipient_ip, recipient_port = self.hub._authenticated_devices[device_id]
                self.hub.send(message, (recipient_ip, int(recipient_port)))
                messagebox.showinfo("Message Sent", f"Message sent successfully to {device_id}.")
            except KeyError:
                messagebox.showerror("Error", f"Device {device_id} not found.")
        else:
            messagebox.showerror("Error", "Device ID and message must be provided.")

    def receive_messages(self):
        while True:
            message, sender_addr = self.hub.receive()
            sender_ip, sender_port = sender_addr
            sender_id = ''
            for id, addr in self.hub._authenticated_devices.items():
                ip, port = addr
                if ip == sender_ip:
                  sender_id = id
                  break

            message = sender_id + ": " + message
            self.display_received_message(message)

    def display_received_message(self, message):
        self.receive_text.config(state="normal")
        self.receive_text.insert(END, message + "\n")
        self.receive_text.config(state="disabled")

    def update_device_list(self):
        self.device_list_text.config(state="normal")
        self.device_list_text.delete(1.0, END)  # Clear existing content

        for device_id, (device_ip, device_port) in self.hub._authenticated_devices.items():
            device_info = f"{device_id} - IP: {device_ip}, Port: {device_port}"
            self.device_list_text.insert(END, device_info + "\n")

        self.device_list_text.config(state="disabled")

    def on_close(self):
        self.root.destroy()
        exit()

def main():
    print("Setting up a new Hub..")
    input_ip = HUB_IP
    input_port = HUB_PORT
    hub = Hub("HUB", input_ip, input_port)

    hub.setEncryption(KEY, upperCaseAll=False, removeSpace=False)

    hub_ui = HubUI(hub)

if __name__ == "__main__":
    main()
