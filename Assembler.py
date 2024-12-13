import struct
import xml.etree.ElementTree as ET
from typing import List, Dict


class Command:
    def __init__(self, opcode: int, b: int, c: int, d: int = None):
        self.opcode = opcode
        self.b = b
        self.c = c
        self.d = d


class VirtualMachine:
    def __init__(self):
        self.memory = {}

    def load_const(self, cmd: Command):
        self.memory[cmd.c] = cmd.b

    def binary_operation(self, cmd: Command):
        value = self.memory.get(cmd.b, 0)

        self.memory[cmd.c] = value
        self.registers[cmd.d] = value

        print(f"Binary operation '>' executed: mem[{cmd.c}] = mem[{cmd.b}] = {value}, reg[{cmd.d}] = {value}")

    def read_memory(self, cmd: Command):
        value = self.memory.get(cmd.c, 0)
        self.memory[cmd.b] = value
        print(f"READ_MEM: mem[{cmd.b}] = mem[{cmd.c}] ({value})")

    def write_memory(self, cmd: Command):

        value = self.memory.get(cmd.c, 0)
        destination_address = self.memory.get(cmd.b,0)
        self.memory[destination_address] = value
        print(f"WRITE_MEM: Writing value {value} to address {destination_address}")

    def binary_operation(self, cmd: Command):
        val1 = self.memory.get(cmd.c, 0)
        val2 = self.memory.get(cmd.d, 0)
        self.memory[cmd.b] = val1 * val2
        print(f"Execution: {val1} * {val2} = {self.memory[cmd.b]} stored at mem[{cmd.b}]")

    def print_memory(self):
        print("Current Memory State:")
        for addr, value in sorted(self.memory.items()):
            print(f"Address: {addr}, Value: {value}")


class Assembler:
    def parse_command(self, line: str) -> bytes:
        parts = line.strip().split()
        if not parts:
            return None

        if parts[0] == "LOAD_CONST":
            # Format: LOAD_CONST B C
            opcode = 31
            b = int(parts[1])
            c = int(parts[2])
            return struct.pack(">BBH", opcode, b, c)

        elif parts[0] == "READ_MEM":
            # Format: READ_MEM B C
            opcode = 48
            b = int(parts[1])
            c = int(parts[2])
            return struct.pack(">BBH", opcode, b, c)

        elif parts[0] == "WRITE_MEM":
            # Format: WRITE_MEM B C
            opcode = 10
            b = int(parts[1])
            c = int(parts[2])
            return struct.pack(">BBH", opcode, b, c)

        elif parts[0] == "MULTIPLY":
            # Format: MULTIPLY B C D
            opcode = 17
            b = int(parts[1])
            c = int(parts[2])
            d = int(parts[3])
            return struct.pack(">BBHH", opcode, b, c, d)

        return None

    def assemble(self, input_file: str, output_file: str, log_file: str):
        binary_data = bytearray()
        log = ET.Element("log")

        with open(input_file, 'r') as f:
            for line in f:
                cmd_bytes = self.parse_command(line)
                if cmd_bytes:
                    binary_data.extend(cmd_bytes)
                    cmd = ET.SubElement(log, "command")
                    cmd.text = line.strip()

        with open(output_file, 'wb') as f:
            f.write(binary_data)

        tree = ET.ElementTree(log)
        tree.write(log_file)


class Interpreter:
    def __init__(self):
        self.vm = VirtualMachine()

    def execute(self, binary_file: str, result_file: str):
        with open(binary_file, 'rb') as f:
            data = f.read()

        pos = 0
        while pos < len(data):
            opcode = data[pos]
            print(f"Executing opcode: {opcode} at position: {pos}")

            if opcode == 31:  # LOAD_CONST
                if len(data) - pos >= 4:
                    b, c = struct.unpack(">BH", data[pos + 1:pos + 4])
                    self.vm.load_const(Command(opcode, b, c))
                    pos += 4
                else:
                    print(f"Not enough data for LOAD_CONST at position {pos}")
                    break

            elif opcode == 48:  # READ_MEM
                if len(data) - pos >= 4:
                    b, c = struct.unpack(">BH", data[pos + 1:pos + 4])
                    self.vm.read_memory(Command(opcode, b, c))
                    pos += 4
                else:
                    print(f"Not enough data for READ_MEM at position {pos}")
                    break


            elif opcode == 10:  # WRITE_MEM
                if len(data) - pos >= 4:
                    b, c = struct.unpack(">BH", data[pos + 1:pos + 4])
                    print(f"Executing WRITE_MEM with B={b} C={c}")  # Логируем перед выполнением
                    self.vm.write_memory(Command(opcode, b, c))
                    pos += 4
                else:
                    print(f"Not enough data for WRITE_MEM at position {pos}")
                    break


            elif opcode == 17:  # Бинарная операция ">"
                if len(data) - pos >= 5:
                    b, c, d = struct.unpack(">HHH", data[pos + 1:pos + 5])
                    self.vm.binary_operation(Command(opcode, b, c, d))
                    pos += 5
                else:
                    print(f"Not enough data for binary operation '>' at position {pos}")
                    break

            else:
                print(f"Unrecognized opcode {opcode} at position {pos}. Skipping.")
                pos += 1

        self.vm.print_memory()


        result = ET.Element("result")
        memory = ET.SubElement(result, "memory")

        for addr, value in sorted(self.vm.memory.items()):
            entry = ET.SubElement(memory, "entry")
            entry.set("address", str(addr))
            entry.set("value", str(value))

        try:
            tree = ET.ElementTree(result)
            tree.write(result_file)
            print(f"Results successfully written to {result_file}.")
        except Exception as e:
            print(f"Error writing result to {result_file}: {e}")



def run_test():
    with open("test.asm", "w") as f:
        f.write("""LOAD_CONST 42 27
READ_MEM 32 27
LOAD_CONST 49 30
WRITE_MEM 30 32
31 48 31 10 48""")


    assembler = Assembler()
    assembler.assemble("test.asm", "program.bin", "assembler.log")

    interpreter = Interpreter()
    interpreter.execute("program.bin", "result.xml")


def execute_program():
    interpreter = Interpreter()
    interpreter.execute("program.bin", "result.xml")

    interpreter.vm.print_memory()

def test_binary_operation():
    vm = VirtualMachine()

    vm.set_memory(110, 42)
    vm.set_memory(70, 0)
    vm.set_register(691, 0)

    cmd = Command(17, 110, 70, 691)
    vm.binary_operation(cmd)

    assert vm.get_memory(70) == 42, "Значение в памяти по адресу 70 должно быть 42"
    assert vm.get_register(691) == 42, "Значение в регистре по адресу 691 должно быть 42"

    print("Тест бинарной операции '>' успешно пройден!")

if __name__ == "__main__":
    run_test()
