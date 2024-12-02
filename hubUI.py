from tkinter import Tk, Label, Entry, Button, Text, Scrollbar, Toplevel, END, messagebox, ttk, StringVar
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
        self.root.geometry("600x500")
        # Device Registration Frame
        reg_frame = ttk.LabelFrame(self.root, text="Device Registration")
        reg_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=8, sticky="nsew")
        Label(reg_frame, text="Device ID:").grid(row=0, column=0, padx=5, pady=5)
        Label(reg_frame, text="Device IP:").grid(row=1, column=0, padx=5, pady=5)
        Label(reg_frame, text="Device Port:").grid(row=2, column=0, padx=5, pady=5)
        Label(reg_frame, text="Location:").grid(row=3, column=0, padx=5, pady=5)

        self.device_id_entry = Entry(reg_frame)
        self.device_ip_entry = Entry(reg_frame)
        self.device_port_entry = Entry(reg_frame)
        self.device_location_entry = Entry(reg_frame)

        self.device_id_entry = Entry(reg_frame)
        self.device_ip_entry = Entry(reg_frame)
        self.device_port_entry = Entry(reg_frame)
        self.device_location_entry = Entry(reg_frame)

        self.device_id_entry.grid(row=0, column=1, padx=5, pady=5)
        self.device_ip_entry.grid(row=1, column=1, padx=5, pady=5)
        self.device_port_entry.grid(row=2, column=1, padx=5, pady=5)
        self.device_location_entry.grid(row=3, column=1, padx=5, pady=5)

        # Buttons
        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)

        self.start_consensus_button = Button(button_frame, text="Start Consensus", command= self.hub.start_consensus_protocol)

        self.add_device_button = Button(button_frame, text="Add Device", command=self.add_device)
        self.send_button = Button(button_frame, text="Send Message", command=self.open_send_message_popup)
        self.view_blockchain_button = Button(button_frame, text="View Blockchain", command=self.view_blockchain)
        
        self.start_consensus_button.pack(side='left', padx=5)
        self.add_device_button.pack(side='left', padx=5)
        self.send_button.pack(side='left', padx=5)
        self.view_blockchain_button.pack(side='left', padx=5)

        # Message Display
        self.receive_text = Text(self.root, height=10, width=70)
        self.device_list_text = Text(self.root, height=5, width=70)
        self.receive_text.config(state="disabled")
        self.device_list_text.config(state="disabled")

        # Device selection for blockchain data display
        self.device_var = StringVar()
        self.blockchain_device_dropdown = ttk.Combobox(self.root, textvariable = self.device_var)
        self.blockchain_device_dropdown.grid(row=2, column=0, columnspan=2, pady=10)

        self.device_list_text.grid(row=3, column=0, columnspan=2, pady=10)

        scrollbar_receive = Scrollbar(self.root, command=self.receive_text.yview)
        scrollbar_device_list = Scrollbar(self.root, command=self.device_list_text.yview)

        scrollbar_receive.grid(row=2, column=2, sticky='nsew')
        scrollbar_device_list.grid(row=3, column=2, sticky='nsew')

        self.receive_text['yscrollcommand'] = scrollbar_receive.set
        self.device_list_text['yscrollcommand'] = scrollbar_device_list.set

        # Start message receiving thread
        receive_thread = Thread(target=self.receive_messages)
        receive_thread.daemon = True
        receive_thread.start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def add_device(self):
        device_id = self.device_id_entry.get()
        device_ip = self.device_ip_entry.get()
        device_port = self.device_port_entry.get()
        location = self.device_location_entry.get()

        if device_id and device_ip and device_port:
            try:
                self.hub.register_device(device_id, device_ip, device_port, location)
                messagebox.showinfo("Device Added", 
                                  f"Device {device_id} added successfully.\n"
                                  f"Location: {location}")
                self.update_device_list()
                
                # Clear entry fields
                self.device_id_entry.delete(0, END)
                self.device_ip_entry.delete(0, END)
                self.device_port_entry.delete(0, END)
                self.device_location_entry.delete(0, END)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add device: {str(e)}")
        else:
            messagebox.showerror("Error", "All fields must be filled.")

    def open_send_message_popup(self):
        popup = Toplevel(self.root)
        popup.title("Send Message")

        popup.geometry("500x300")
        # Get list of registered devices
        devices = list(self.hub._authenticated_devices.keys())
        
        # Device selection
        Label(popup, text="Select Device:").grid(row=0, column=0, padx=5, pady=5)
        device_var = ttk.Combobox(popup, values=devices)
        device_var.grid(row=0, column=1, padx=5, pady=5)
        
        # Command selection
        Label(popup, text="Command:").grid(row=1, column=0, padx=5, pady=10)
        command_entry = Entry(popup)
        command_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Parameter input
        Label(popup, text="Parameter (optional):").grid(row=2, column=0, padx=5, pady=5)
        param_entry = Entry(popup)
        param_entry.grid(row=2, column=1, padx=5, pady=5)
        # Help text
        help_text = Text(popup, height=8, width=60)
        help_text.grid(row=3, column=0, columnspan=5, padx=6, pady=8)
        help_text.insert(END, "Common Commands:\n\n"
                        "Cameras: get_status, set_status, get_location\n"
                        "DoorLocks: get_state, set_state, get_status, set_status\n"
                        "Thermostats: get_temperature, set_temperature, get_status\n\n"
                        "Use semicolon (;) to separate command and parameter")
        help_text.config(state="disabled")
        # Send button
        send_button = Button(popup, text="Send", 
                           command=lambda: self.send_message_popup(
                               device_var.get(),
                               f"{command_entry.get()};{param_entry.get()}" if param_entry.get() 
                               else command_entry.get(),
                               popup))
        send_button.grid(row=4, column=0, columnspan=2, pady=10)

    def send_message_popup(self, device_id, message, popup):
        popup.destroy()

        if device_id and message:
            try:
                recipient_ip, recipient_port = self.hub._authenticated_devices[device_id]
                self.hub.send(message, (recipient_ip, int(recipient_port)))
                messagebox.showinfo("Message Sent", f"Message sent successfully to {device_id}.")
            except KeyError:
                messagebox.showerror("Error", f"Device {device_id} not found.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to send message: {str(e)}")
        else:
            messagebox.showerror("Error", "Device ID and message must be provided.")

    def receive_messages(self):
        while True:
            try:
                message, sender_addr = self.hub.receive()
                self.display_received_message(message)
            except Exception as e:
                print(f"Error in receive_messages: {e}")
                continue

    def display_received_message(self, message):
        try:
            self.receive_text.config(state="normal")
            self.receive_text.insert(END, f"{message}\n")
            self.receive_text.see(END)
            self.receive_text.config(state="disabled")
        except Exception as e:
            print(f"Error displaying message: {e}")

    def update_device_list(self):
        self.device_list_text.config(state="normal")
        self.device_list_text.delete(1.0, END)

        for device_id, (device_ip, device_port) in self.hub._authenticated_devices.items():
            location = self.hub.get_device_location(device_id)
            device_info = f"{device_id} - IP: {device_ip}, Port: {device_port}, Location: {location}\n"
            self.device_list_text.insert(END, device_info)

        self.device_list_text.config(state="disabled")

        #update device dropdown for blockchain view
        device_ids = list(self.hub._authenticated_devices.keys())
        self.blockchain_device_dropdown['values'] = device_ids
        if device_ids:
            self.blockchain_device_dropdown.set(device_ids[0])

    def view_blockchain(self):
        selected_device = self.device_var.get()
        if not selected_device:
            messagebox.showerror("Error", "Please select a device.")
            return

        blockchain_window = Toplevel(self.root)
        blockchain_window.title(f"Blockchain View - {selected_device}")
        blockchain_window.geometry("800x600")

        blockchain_text = Text(blockchain_window, wrap="word", height=30, width=90)
        scrollbar = Scrollbar(blockchain_window, command=blockchain_text.yview)
        blockchain_text.configure(yscrollcommand=scrollbar.set)
        blockchain_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def update_blockchain_view(): 
            try: 
                # Get the current selection each time we update
                current_device = self.device_var.get()
                blockchain_data = self.hub.get_blockchain_data(current_device)
                blockchain_text.config(state="normal")
                blockchain_text.delete(1.0, END)

                if not blockchain_data:
                    blockchain_text.insert(END, "No blockchain data found")
                else:
                    for block in blockchain_data:
                        blockchain_text.insert(END, f"\nBlock {block['index']}:\n")
                        blockchain_text.insert(END, f"Timestamp: {block['timestamp']}\n")
                        blockchain_text.insert(END, f"Previous Hash: {block['previous_hash']}\n")
                        blockchain_text.insert(END, f"Interactions: {block['interactions']}\n")

                blockchain_text.config(state="disabled")
                
            except Exception as e:
                    blockchain_text.config(state="normal")
                    blockchain_text.delete(1.0, END)
                    blockchain_text.insert(END, f"Error retrieving blockchain data: {str(e)}\n")
                    blockchain_text.config(state="disabled")
            
            if blockchain_window.winfo_exists():  # Only schedule next update if window still exists
                    blockchain_window.after(5000, update_blockchain_view)

        update_blockchain_view()    

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