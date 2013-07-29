from winappdbg import Debug, EventHandler, HexDump, CrashDump, win32
import hashlib
import sys
import time
import json
import base64
import binascii
import sqlite3
import zlib
import multiprocessing

PROGRAM_PATH = 'path_to_executable'
ARGUMENTS = [
     'path_to_first_argument'
]
DB_NAME = 'path_to_output.json'


class StepWriter :
    def __init__ (self, filename) :
        self.hashes = {}
        self.block_size = 8192
        self.filename = filename

        fh = open(filename, 'w')
        fh.write('')
        fh.close()

    def write_step (self, thread_id, module_name, label, instruction_bin, instruction_text, registers, stack_mem, stack_trace) :
        step = {}
        step['type'] = 'step'
        step['thread_id'] = thread_id
        step['module'] = module_name
        step['label'] = label
        step['instruction_bin'] = binascii.hexlify(instruction_bin)
        step['instruction_text'] = instruction_text
        step['eip'] = registers['Eip']
        step['eax'] = registers['Eax']
        step['ebx'] = registers['Ebx']
        step['ecx'] = registers['Ecx']
        step['edx'] = registers['Edx']
        step['edi'] = registers['Edi']
        step['esi'] = registers['Esi']
        step['ebp'] = registers['Ebp']
        step['esp'] = registers['Esp']
        step['stack_memory'] = base64.b64encode(stack_mem)
        step['stack_trace'] = stack_trace

        fh = open(self.filename, 'a')
        fh.write(json.dumps(step) + '\n')
        fh.close()

    def write_event (self, event_name, event_details) :
        return

    def update_block (self, step_id, address, data) :
        return

    def write_memory_map (self, step_id, memory_map) :
        return



stepWriter = StepWriter(DB_NAME)
steps = 0

class Tracer (EventHandler) :

    def create_process (self, event) :
        event.debug.start_tracing(event.get_tid())

    def create_thread (self, event) :
        event.debug.start_tracing(event.get_tid())

    def single_step (self, event) :
        thread = event.get_thread()
        pc = thread.get_pc()
        code = thread.disassemble(pc, 0x10)[0]
        bits = event.get_process().get_bits()
        process = event.get_process()

        process.scan_modules()

        global stepWriter, steps
        stepWriter.write_step(thread.get_tid(), \
                              process.get_module_at_address(pc).get_name(), \
                              process.get_label_at_address(pc), \
                              process.read(pc, code[1]), \
                              code[2], \
                              thread.get_context(), \
                              process.read(thread.get_sp() - 124, 128), \
                              thread.get_stack_trace_with_labels())
        steps += 1
        if steps & 0xff == 0:
            print steps

    def event (self, event) :
        return
        global stepWriter
        if event.get_event_name() == 'Exception event' :
            stepWriter.write_event(event.get_exception_name(), event.get_exception_description())
        else :
            stepWriter.write_event(event.get_event_name(), event.get_event_description())

def simple_debugger (args) :
    with Debug(Tracer(), bKillOnExit = True) as debug :
        process = debug.execv(args)
        debug.loop()

simple_debugger([PROGRAM_PATH] + ARGUMENTS)