import xml.etree.ElementTree as ET
import argparse
import sys
import re
from exit_codes import ExitCodes as ec


class Interpret:

    def __init__(self):
        self.arguments = self.process_arguments()
        if (self.arguments.source == self.arguments.input):
            sys.stderr.write("Invalid arguments\n")
            exit(ec.ARGUMENT_ERROR)
        self.input_string = self.read_input()
        xml_string = self.read_xml_source()
        try:
            self.root = ET.fromstring(xml_string)
        except ET.ParseError:
            sys.stderr.write("Input XML not well formed\n")
            exit(ec.XML_NOT_WELL_FORMED_ERROR)

        self.temporary_frame = None
        self.local_frame_stack = []
        self.global_frame = []
        self.data_stack = []
        self.labels = []

    def read_xml_source(self):
        """
        Read xml source file or stdin, based on arguments given to the script
        Returns a string representation of the xml
        """
        if self.arguments.source:
            try:
                with open(self.arguments.source, 'r') as source:
                    xml_string = source.read()
            except FileNotFoundError:
                sys.stderr.write(f"Input file '{self.arguments.source}' not found\n")
                exit(ec.INPUT_FILE_ERROR)
        else:
            xml_string = sys.stdin.read()  # todo handle error
        return xml_string

    def read_input(self):
        """
        Read input file or stdin, based on arguments given to the script
        Returns a string representation of the input data
        """
        if self.arguments.input:
            try:
                with open(self.arguments.input, 'r') as source:
                    input_string = source.read()
            except FileNotFoundError:
                sys.stderr.write(f"Input file '{self.arguments.input}' not found\n")
                exit(ec.INPUT_FILE_ERROR)
        else:
            input_string = sys.stdin.read()
        return input_string

    def process_arguments(self):
        """
        Read arguments given to the script and return them
        Also create a simle help interface (accessible with -h, --help)
        """
        argument_parser = argparse.ArgumentParser(
            description="The interpreter executes scripts written in XML representation of IPPcode20.")
        argument_parser.add_argument(
            "--source", type=str,
            help="path to source file containing the XML representation of IPPcode20")
        argument_parser.add_argument(
            "--input", type=str,
            help="path to input file containing program input of the executed IPPcode20 script.")
        return argument_parser.parse_args()

    def check_xml_structure(self):
        """
        Control 
        """
        self.check_root_element()
        # todo check other stuff

    def check_root_element(self):
        """
        Control if the root element of the xml is valid
        """
        if not re.match("^program$", self.root.tag, re.I):
            sys.stderr.write(f"Expected root element to be 'program', found '{self.root.tag}'\n")
            exit(ec.XML_WRONG_STRUCTURE_ERROR)

        if len(self.root.attrib) < 1 or len(self.root.attrib) > 3:
            sys.stderr.write("Ivalid attributes of 'program' element\n")
            exit(ec.XML_WRONG_STRUCTURE_ERROR)

        allowed_attributes = ['language', 'name', 'description']
        for attr in self.root.attrib:
            if attr not in allowed_attributes:
                sys.stderr.write("Ivalid attributes of 'program' element\n")
                exit(ec.XML_WRONG_STRUCTURE_ERROR)

        if not ("language" in self.root.attrib and re.match("^ippcode20$", self.root.attrib["language"], re.I)):
            sys.stderr.write("Expected 'program' element attribute to be 'language=ippcode20'\n")
            exit(ec.XML_WRONG_STRUCTURE_ERROR)

    def execute(self):
        """
        Interpret source code.
        """
        print("--------RUN--------")
        # print(self.root.tag) todo delete
        # print(type(self.root.attrib))
        # todo lexical and syntactival analysis
        # sorted = self.root.
        # f = itemgetter('order')
        # for element in self.root:
        #     print(f(element.attrib))
        # sorted = self.root.findall('instruction').sort()
        # print(f())
        # parent = self.root
        # attr = 'order'
        try:
            self.root[:] = sorted(self.root, key=lambda child: int(child.get('order')))  # todo check double value abd negative values
        except ValueError:
            sys.stderr.write("Order attribute value not valid\n")
            exit(ec.XML_WRONG_STRUCTURE_ERROR)

        # print(self.input_string)
        # interpretation body
        self.i = 0
        while self.i < len(self.root):
            element = self.root[self.i]
            instruction = Instruction(element, self.i)
            instruction_handler = self.instruction_swticher(instruction.opcode)
            instruction_handler(instruction)
            self.i += 1
            # todo jump to not discovered labels

        print("--------END--------")

    def instruction_swticher(self, opcode):
        """
        Returns the function that should be called based on the given opcode.
        """
        if opcode == "MOVE":
            return self.ins_move
        elif opcode == "CREATEFRAME":
            return self.ins_create_frame
        elif opcode == "PUSHFRAME":
            return self.ins_push_frame
        elif opcode == "POPFRAME":
            return self.ins_pop_frame
        elif opcode == "DEFVAR":
            return self.ins_defvar
        elif opcode == "WRITE":
            return self.ins_write
        elif opcode == "LABEL":
            return self.ins_label
        elif opcode == "JUMP":
            return self.ins_jump
        else:
            sys.stderr.write(f"Opcode {opcode} not valid\n")
            exit(ec.XML_WRONG_STRUCTURE_ERROR)

    def ins_move(self, ins):
        """
        Execute MOVE instruction
        """
        pass

    def ins_create_frame(self, ins):
        """
        Execute CREATEFRAME instruction
        """
        self.temporary_frame = []

    def ins_push_frame(self, ins):
        """
        Execute PUSHFRAME instruction
        """
        if self.temporary_frame is None:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Temporary frame not defined.\n")
            exit(ec.RUNTIME_UNDEFINED_FRAME_ERROR)
        self.local_frame_stack.append(self.temporary_frame)
        self.temporary_frame = None

    def ins_pop_frame(self, ins):
        """
        Execute POPFRAME instruction
        """
        if len(self.local_frame_stack) == 0:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Local frame stack is empty.\n")
            exit(ec.RUNTIME_UNDEFINED_FRAME_ERROR)
        self.temporary_frame = self.local_frame_stack.pop()

    def ins_defvar(self, ins):
        """
        Execute DEFVAR instruction
        """
        frame, variable_name = ins.arg1[1].split("@")
        if frame == "GF":
            if any(variable["name"] == variable_name for variable in self.global_frame):
                sys.stderr.write(f"({ins.order}){ins.opcode}: Variable '{variable_name}' already exists in global context.\n")
                exit(ec.SEMANTIC_ERROR)
            self.global_frame.append({"name": variable_name, "value": None})
        elif frame == "LF":
            if len(self.local_frame_stack) == 0:
                sys.stderr.write(f"({ins.order}){ins.opcode}: Local frame not defined.\n")
                exit(ec.RUNTIME_UNDEFINED_FRAME_ERROR)
            if any(variable["name"] == variable_name for variable in self.local_frame_stack[-1]):
                sys.stderr.write(f"({ins.order}){ins.opcode}: Variable '{variable_name}' already exists in local context.\n")
                exit(ec.SEMANTIC_ERROR)
            self.local_frame_stack[-1].append({"name": variable_name, "value": None})
        elif frame == "TF":
            if self.temporary_frame is None:
                sys.stderr.write(f"({ins.order}){ins.opcode}: Temporary frame not defined.\n")
                exit(ec.RUNTIME_UNDEFINED_FRAME_ERROR)
            if any(variable["name"] == variable_name for variable in self.temporary_frame):
                sys.stderr.write(f"({ins.order}){ins.opcode}: Variable '{variable_name}' already exists in temporary context.\n")
                exit(ec.SEMANTIC_ERROR)
            self.temporary_frame.append({"name": variable_name, "value": None})
        else:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Local frame stack is empty.\n")
            exit(ec.XML_WRONG_STRUCTURE_ERROR)

    def ins_call(self, ins):
        """
        Execute CALL instruction
        """
        pass

    def ins_return(self, ins):
        """
        Execute RETURN instruction
        """
        pass

    def ins_pushs(self, ins):
        """
        Execute PUSHS instruction
        """
        self.data_stack.append('todo')
        pass

    def ins_pops(self, ins):
        """
        Execute POPS instruction
        """
        pass

    # todo more functions

    def ins_write(self, ins):
        """
        Execute WRITE instruction
        """
        print(ins.arg1[1])  # todo finish

    # todo more functions

    def ins_label(self, ins):
        """
        Execute LABEL instruction
        """
        self.labels.append({"name": ins.arg1[1], "index": ins.real_order})

    def ins_jump(self, ins):
        """
        Execute JUMP instruction
        """
        self.i = int(next(label for label in self.labels if label["name"] == ins.arg1[1])["index"]) - 1


class Instruction:
    """
    Encapsulates information of the instruction.
    An instance should be created for each processed instruction.
    """

    def __init__(self, instruction_element, i):
        self.opcode = instruction_element.attrib['opcode']
        self.order = instruction_element.attrib['order']
        self.real_order = i
        # arguments are tuples (type, value)
        arg_element = instruction_element.find("arg1")
        self.arg1 = (arg_element.attrib['type'], arg_element.text) if arg_element is not None else None

        arg_element = instruction_element.find("arg2")
        self.arg2 = (instruction_element.find("arg2"), arg_element.text) if arg_element is not None else None

        arg_element = instruction_element.find("arg3")
        self.arg3 = (instruction_element.find("arg3"), arg_element.text) if arg_element is not None else None

    # todo lex and syn control


interpret = Interpret()
interpret.check_xml_structure()
interpret.execute()
