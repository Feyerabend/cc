import os
import machine, sdcard
import utime, uos

# chip select (CS) pin (start high)
cs = machine.Pin(1, machine.Pin.OUT)

# init SPI peripheral (start with 1 MHz)
spi = machine.SPI(0,
                  baudrate=1000000,
                  polarity=0,
                  phase=0,
                  bits=8,
                  firstbit=machine.SPI.MSB,
                  sck=machine.Pin(2),
                  mosi=machine.Pin(3),
                  miso=machine.Pin(4))

# init SD card
sd = sdcard.SDCard(spi, cs)

# mount filesystem
vfs = uos.VfsFat(sd)
uos.mount(vfs, "/sd")



# simple database -- slightly better security
class MiniDB:
    def __init__(self, base="/sd", flush_every=1):
        # base = directory where .csv tables are stored
        self.base = base if base.endswith("/") else base + "/"
        self.flush_every = max(1, flush_every)
        self.buffers = {}  # table_name -> list of rows

        # check that base exists
        try:
            os.listdir(self.base)
        except OSError:
            raise RuntimeError("Base path not available: " + self.base)

    def _path(self, name):
        return self.base + name + ".csv"

    def create_table(self, name, fields):
        """Create a new table. Overwrites if exists."""
        try:
            with open(self._path(name), "w") as f:
                f.write(",".join(fields) + "\n")
                f.flush()
            self.buffers[name] = []
            return True
        except OSError:
            return False

    def insert(self, name, row):
        """Insert a row into buffer. Flush if buffer is full."""
        if not isinstance(row, (list, tuple)):
            return False
        if name not in self.buffers:
            self.buffers[name] = []
        self.buffers[name].append(row)
        if len(self.buffers[name]) >= self.flush_every:
            return self.commit(name)
        return True

    def commit(self, name):
        """Flush buffer for a table."""
        if name not in self.buffers or not self.buffers[name]:
            return False
        try:
            with open(self._path(name), "a") as f:
                for row in self.buffers[name]:
                    f.write(",".join(str(x) for x in row) + "\n")
                f.flush()
            self.buffers[name] = []
            return True
        except OSError:
            return False

    def all_rows(self, name):
        """Generator over all rows as dicts. Returns empty if file missing."""
        try:
            with open(self._path(name), "r") as f:
                header = f.readline().strip().split(",")
                if not header or header == ['']:
                    return
                for line in f:
                    values = line.strip().split(",")
                    if values == [''] or len(values) != len(header):
                        continue
                    yield dict(zip(header, values))
        except OSError:
            return

    def select(self, name, where=None):
        """Select rows (dicts)."""
        for row in self.all_rows(name) or []:
            if where:
                if all(row.get(k) == str(v) for k, v in where.items()):
                    yield row
            else:
                yield row

    def delete_table(self, name):
        """Delete entire table file + buffer."""
        try:
            os.remove(self._path(name))
        except OSError:
            return False
        if name in self.buffers:
            del self.buffers[name]
        return True

    def delete_rows(self, name, where=None):
        """Delete rows matching condition. Skip if table missing/empty."""
        path = self._path(name)
        try:
            with open(path, "r") as f:
                header = f.readline().strip()
                if not header:
                    return False
                header_fields = header.split(",")
                rows = []
                deleted = False
                for line in f:
                    values = line.strip().split(",")
                    if len(values) != len(header_fields):
                        continue
                    row = dict(zip(header_fields, values))
                    keep = True
                    if where:
                        if all(row.get(k) == str(v) for k, v in where.items()):
                            keep = False
                            deleted = True
                    if keep:
                        rows.append(values)
        except OSError:
            return False

        if not deleted:
            return False  # nothing removed

        # rewrite file
        try:
            with open(path, "w") as f:
                f.write(header + "\n")
                for values in rows:
                    f.write(",".join(values) + "\n")
                f.flush()
            return True
        except OSError:
            return False

    def count(self, name, where=None):
        """Count rows, optionally filtered."""
        cnt = 0
        for _ in self.select(name, where):
            cnt += 1
        return cnt



db = MiniDB("/sd", flush_every=3)

db.create_table("temperature", ["time", "temp"])
db.insert("temperature", [1, 22.1])
db.insert("temperature", [2, 22.3])
db.insert("temperature", [3, 22.5])  # triggers commit
db.commit("temperature")             # make sure buffer is flushed

print("Row count:", db.count("temperature"))
for r in db.all_rows("temperature"):
    print(r)

print("Deleting one row:", db.delete_rows("temperature", where={"temp":"22.3"}))
print("Row count after delete:", db.count("temperature"))

print("Deleting table:", db.delete_table("temperature"))
