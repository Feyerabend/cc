import machine
import sdcard
import uos
import ujson
import utime

class SimpleVFS:
    
    def __init__(self, mount_point="/sd"):
        self.mount_point = mount_point
        self.metadata_file = f"{mount_point}/.vfs_metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self):
        try:
            with open(self.metadata_file, "r") as f:
                return ujson.load(f)
        except:
            return {}
    
    def _save_metadata(self):
        with open(self.metadata_file, "w") as f:
            ujson.dump(self.metadata, f)
    
    def create_file(self, filename, data, permissions="rw"):
        full_path = f"{self.mount_point}/{filename}"
        
        # Write the actual file
        with open(full_path, "wb") as f:
            if isinstance(data, str):
                f.write(data.encode())
            else:
                f.write(data)
        
        # Store metadata
        self.metadata[filename] = {
            "permissions": permissions,
            "created": utime.time(),
            "size": len(data)
        }
        self._save_metadata()
        print(f"Created file: {filename} ({len(data)} bytes)")
    
    def read_file(self, filename):
        if filename not in self.metadata:
            raise FileNotFoundError(f"File '{filename}' not found in VFS")
        
        if 'r' not in self.metadata[filename]["permissions"]:
            raise OSError(f"No read permission for '{filename}'")
        
        full_path = f"{self.mount_point}/{filename}"
        with open(full_path, "rb") as f:
            return f.read()
    
    def write_file(self, filename, data):
        if filename not in self.metadata:
            raise FileNotFoundError(f"File '{filename}' not found in VFS")
        
        if 'w' not in self.metadata[filename]["permissions"]:
            raise OSError(f"No write permission for '{filename}'")
        
        full_path = f"{self.mount_point}/{filename}"
        with open(full_path, "wb") as f:
            if isinstance(data, str):
                f.write(data.encode())
            else:
                f.write(data)
        
        # Update metadata
        self.metadata[filename]["size"] = len(data)
        self.metadata[filename]["modified"] = utime.time()
        self._save_metadata()
    
    def list_files(self):
        files = []
        for filename, meta in self.metadata.items():
            files.append({
                "name": filename,
                "size": meta["size"],
                "permissions": meta["permissions"],
                "created": meta.get("created", 0)
            })
        return files
    
    def delete_file(self, filename):
        if filename not in self.metadata:
            raise FileNotFoundError(f"File '{filename}' not found in VFS")
        
        full_path = f"{self.mount_point}/{filename}"
        uos.remove(full_path)
        del self.metadata[filename]
        self._save_metadata()
        print(f"Deleted file: {filename}")
    
    def set_permissions(self, filename, permissions):
        """Change file permissions"""
        if filename not in self.metadata:
            raise FileNotFoundError(f"File '{filename}' not found in VFS")
        
        self.metadata[filename]["permissions"] = permissions
        self._save_metadata()
        print(f"Changed permissions of '{filename}' to '{permissions}'")
    
    def get_stats(self):
        total_files = len(self.metadata)
        total_size = sum(meta["size"] for meta in self.metadata.values())
        
        # Get actual SD card stats
        try:
            statvfs = uos.statvfs(self.mount_point)
            block_size = statvfs[0]
            total_blocks = statvfs[2] 
            free_blocks = statvfs[3]
            total_space = total_blocks * block_size
            free_space = free_blocks * block_size
        except:
            total_space = free_space = 0
        
        return {
            "files": total_files,
            "used_by_vfs": total_size,
            "total_space": total_space,
            "free_space": free_space
        }

# Use with existing setup:
try:
    cs = machine.Pin(1, machine.Pin.OUT)
    spi = machine.SPI(0,
                      baudrate=1000000,
                      polarity=0,
                      phase=0,
                      bits=8,
                      firstbit=machine.SPI.MSB,
                      sck=machine.Pin(2),
                      mosi=machine.Pin(3),
                      miso=machine.Pin(4))
    sd = sdcard.SDCard(spi, cs)
    vfs = uos.VfsFat(sd)
    uos.mount(vfs, "/sd")
except OSError as e:
    print(f"Failed to initialize or mount SD card: {e}")
    raise  # Re-raise to stop execution if SD card fails

# Educational VFS wrapper
simple_vfs = SimpleVFS("/sd")

# Abstracted interface
simple_vfs.create_file("hello.txt", "Hello World!", permissions="rw")
simple_vfs.create_file("secret.txt", "Top Secret", permissions="r")  # Read-only

print("Files:", simple_vfs.list_files())
print("Content:", simple_vfs.read_file("hello.txt").decode())

# Write to read-only file (will fail)
try:
    simple_vfs.write_file("secret.txt", "Modified")
except OSError as e:
    print("Permission denied:", e)

print("Stats:", simple_vfs.get_stats())
