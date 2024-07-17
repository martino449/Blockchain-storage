try:
    import hashlib
    import datetime
    import json
    import threading
    import time
    from cryptography.fernet import Fernet
    import tkinter as tk
    from tkinter import scrolledtext, messagebox

    print("All libraries are installed correctly.")
except ImportError as e:
    print(f"Library not installed: {e}")

# Funzione per generare e salvare una nuova chiave crittografica in modo sicuro
def generate_key():
    key = Fernet.generate_key()
    cipher_suite = Fernet(key)
    return key, cipher_suite

# Funzione per caricare la chiave crittografica
def load_key():
    try:
        with open('secret.key', 'rb') as key_file:
            key = key_file.read()
        return key
    except FileNotFoundError:
        # Se il file non esiste, genera una nuova chiave
        key, _ = generate_key()
        with open('secret.key', 'wb') as key_file:
            key_file.write(key)
        return key

# Carica la chiave crittografica al momento dell'esecuzione del programma
key = load_key()
cipher_suite = Fernet(key)

class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.data_hash = self.hash_data()
        self.hash = self.hash_block()

    def hash_data(self):
        sha = hasher.sha256()
        sha.update(str(self.data).encode('utf-8'))
        return sha.hexdigest()

    def hash_block(self):
        sha = hasher.sha256()
        sha.update(str(self.index).encode('utf-8') +
                   str(self.timestamp).encode('utf-8') +
                   str(self.data_hash).encode('utf-8') +
                   str(self.previous_hash).encode('utf-8'))
        return sha.hexdigest()

    @staticmethod
    def next_block(last_block, data):
        this_index = last_block.index + 1
        this_timestamp = date.datetime.now()
        this_hash = last_block.hash
        return Block(this_index, this_timestamp, data, this_hash)

    @staticmethod
    def create_genesis():
        return Block(0, date.datetime.now(), "Genesis Block", "0")

def save_blockchain(blockchain):
    blockchain_data = []
    for block in blockchain:
        block_data = {
            'index': block.index,
            'timestamp': str(block.timestamp),
            'data': block.data,
            'data_hash': block.data_hash,
            'previous_hash': block.previous_hash,
            'hash': block.hash
        }
        blockchain_data.append(block_data)

    json_data = json.dumps(blockchain_data, indent=4)
    encrypted_data = cipher_suite.encrypt(json_data.encode('utf-8'))

    with open('blockchain.json', 'wb') as file:
        file.write(encrypted_data)

def load_blockchain():
    try:
        with open('blockchain.json', 'rb') as file:
            encrypted_data = file.read()

        decrypted_data = cipher_suite.decrypt(encrypted_data).decode('utf-8')
        blockchain_data = json.loads(decrypted_data)

        blockchain = []
        for block_data in blockchain_data:
            block = Block(
                block_data['index'],
                date.datetime.strptime(block_data['timestamp'], '%Y-%m-%d %H:%M:%S.%f'),
                block_data['data'],
                block_data['previous_hash']
            )
            block.data_hash = block_data['data_hash']  # Restore data_hash from saved data
            block.hash = block_data['hash']  # Restore hash from saved data
            blockchain.append(block)

        return blockchain

    except FileNotFoundError:
        return []

def check_integrity(blockchain):
    for i in range(1, len(blockchain)):
        current_block = blockchain[i]
        previous_block = blockchain[i - 1]

        if current_block.previous_hash != previous_block.hash:
            return False

        if current_block.data_hash != current_block.hash_data():
            return False

        if current_block.hash != current_block.hash_block():
            return False

    return True

def recalculate_hashes_and_check(blockchain):
    for block in blockchain:
        if block.hash != block.hash_block():
            return False
    return True

blockchain = load_blockchain()
if not blockchain:
    blockchain = [Block.create_genesis()]

previous_block = blockchain[-1]

# GUI implementation
def add_block():
    global previous_block
    data = data_entry.get()
    block_to_add = Block.next_block(previous_block, data)
    blockchain.append(block_to_add)
    previous_block = block_to_add
    display_blockchain()
    if check_integrity(blockchain):
        messagebox.showinfo("Success", f"Block #{block_to_add.index} has been added to the blockchain!")
    else:
        messagebox.showerror("Error", "Blockchain integrity check failed.")

def display_blockchain():
    blockchain_text.config(state=tk.NORMAL)
    blockchain_text.delete(1.0, tk.END)
    for block in blockchain:
        blockchain_text.insert(tk.END, f"Index: {block.index}\n")
        blockchain_text.insert(tk.END, f"Timestamp: {block.timestamp}\n")
        blockchain_text.insert(tk.END, f"Data: {block.data}\n")
        blockchain_text.insert(tk.END, f"Data Hash: {block.data_hash}\n")
        blockchain_text.insert(tk.END, f"Block Hash: {block.hash}\n")
        blockchain_text.insert(tk.END, "------------------\n")
    blockchain_text.config(state=tk.DISABLED)

def save_blockchain_gui():
    if check_integrity(blockchain):
        save_blockchain(blockchain)
        messagebox.showinfo("Success", "Blockchain saved to blockchain.json")
    else:
        messagebox.showerror("Error", "Blockchain integrity check failed. Not saving the blockchain.")

def check_integrity_gui():
    if check_integrity(blockchain):
        messagebox.showinfo("Success", "Blockchain integrity verified. No errors found.")
    else:
        messagebox.showerror("Error", "Blockchain integrity check failed.")

# Background integrity check function
def background_integrity_check():
    while True:
        time.sleep(60)  # Check every 60 seconds
        if not check_integrity(blockchain) or not recalculate_hashes_and_check(blockchain):
            messagebox.showerror("Error", "Blockchain integrity check failed in background.")
            break

# Start background integrity check thread
integrity_check_thread = threading.Thread(target=background_integrity_check, daemon=True)
integrity_check_thread.start()

# Create the main window
root = tk.Tk()
root.title("Blockchain Datastorage by Martin449")

# Create and place widgets
data_label = tk.Label(root, text="Enter data for the new block:")
data_label.pack()

data_entry = tk.Entry(root, width=50)
data_entry.pack()

add_block_button = tk.Button(root, text="Add Block", command=add_block)
add_block_button.pack()

save_button = tk.Button(root, text="Save Blockchain", command=save_blockchain_gui)
save_button.pack()

check_integrity_button = tk.Button(root, text="Check Blockchain Integrity", command=check_integrity_gui)
check_integrity_button.pack()

blockchain_text = scrolledtext.ScrolledText(root, width=60, height=20, state=tk.DISABLED)
blockchain_text.pack()

# Display the blockchain initially
display_blockchain()

# Run the main loop
root.mainloop()
