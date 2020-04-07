import xml.etree.ElementTree as ET
import argparse
import sys
import re
from exit_codes import ExitCodes as ec
from operator import itemgetter


class Interpret:

    def __init__(self):
        self.arguments = self.process_arguments()
        if (self.arguments.source == self.arguments.input):
            sys.stderr.write("Invalid arguments\n")
            exit(ec.ARGUMENT_ERROR)
        self.input_list = self.read_input()
        xml_string = self.read_xml_source()
        try:
            self.root = ET.fromstring(xml_string)
        except ET.ParseError:
            sys.stderr.write("Input XML not well formed\n")
            exit(ec.XML_NOT_WELL_FORMED_ERROR)

        self.instructions = []
        # self.temporary_frame = None
        self.local_frame_stack = []
        # self.global_frame = dict()
        self.data_stack = []
        self.labels = dict()
        self.call_stack = []

        self.frames = {
            "GF": dict(),
            "LF": None,
            "TF": None
        }

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
        Read input file and return a list of lines of the input data
        """
        if self.arguments.input:
            try:
                with open(self.arguments.input, 'r') as source:
                    input_list = source.readlines()
                input_list.reverse()
            except FileNotFoundError:
                sys.stderr.write(f"Input file '{self.arguments.input}' not found\n")
                exit(ec.INPUT_FILE_ERROR)
        else:
            input_list = None
        return input_list

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

    def extract_value_from_symbol(self, ins, symbol_type, symbol_value):
        if symbol_type == "var":  # variable
            frame, variable_name = symbol_value.split("@")
            try:
                var_value = self.frames[frame][variable_name]
                if var_value == (None, False):
                    sys.stderr.write(f"({ins.order}){ins.opcode}: Unknown variable '{variable_name}'.\n")
                    exit(ec.RUNTIME_UNDEFINED_VARIABLE_ERROR)
            except KeyError:
                sys.stderr.write(f"({ins.order}){ins.opcode}: Unknown variable '{variable_name}'.\n")
                exit(ec.RUNTIME_UNDEFINED_VARIABLE_ERROR)
            return var_value
        elif symbol_type == "string":
            return str(symbol_value)
        if symbol_type == "int":
            return int(symbol_value)
        if symbol_type == "bool":
            return True if symbol_value == "true" else False
        elif symbol_type == "nil":
            return (None, True)
        else:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Unknown type '{symbol_type}'.\n")
            exit(ec.SEMANTIC_ERROR)

    def execute(self):
        """
        Interpret source code.
        """
        print("--------RUN--------")

        # interpretation body
        self.i = 0
        while self.i < len(self.instructions):
            instruction = self.instructions[self.i]
            instruction_handler = self.instruction_swticher(instruction.opcode)
            instruction_handler(instruction)
            self.i += 1
            # todo jump to not discovered labels

        print("--------END--------")

    def create_instructions_array(self):
        for element in self.root:
            self.instructions.append(Instruction(element))

        self.instructions.sort(key=lambda x: x.order)

        for i, ins in enumerate(self.instructions):
            ins.real_order = i

    def search_labels(self):
        for i, ins in enumerate(self.instructions):
            if ins.opcode == "LABEL":
                if ins.arg1_value in self.labels:
                    sys.stderr.write(f"({ins.order}){ins.opcode}: Cannot redefine label.\n")
                    exit(ec.SEMANTIC_ERROR)
                self.labels[ins.arg1_value] = ins.real_order

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
        elif opcode == "CALL":
            return self.ins_call
        elif opcode == "RETURN":
            return self.ins_return
        elif opcode == "PUSHS":
            return self.ins_pushs
        elif opcode == "POPS":
            return self.ins_pops
        elif opcode in ["ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR"]:
            return self.ins_math_or_logical_operation
        elif opcode == "NOT":
            return self.ins_not
        elif opcode == "INT2CHAR":
            return self.ins_int2char
        elif opcode == "STRI2INT":
            return self.ins_stri2int
        elif opcode == "READ":
            return self.ins_read
        elif opcode == "WRITE":
            return self.ins_write
        elif opcode == "LABEL":
            return self.ins_label
        elif opcode == "JUMP":
            return self.ins_jump
        elif opcode == "EXIT":
            return self.ins_exit
        else:
            sys.stderr.write(f"Opcode {opcode} not valid\n")
            exit(ec.XML_WRONG_STRUCTURE_ERROR)

    # functions for instuction handling

    def ins_move(self, ins):
        """
        Execute MOVE instruction
        """
        dst_frame, dst_var_name = ins.arg1_value.split("@")
        self.frames[dst_frame][dst_var_name] = self.extract_value_from_symbol(ins, ins.arg2_type, ins.arg2_value)

    def ins_create_frame(self, ins):
        """
        Execute CREATEFRAME instruction
        """
        self.frames["TF"] = dict()

    def ins_push_frame(self, ins):
        """
        Execute PUSHFRAME instruction
        """
        if self.frames["TF"] is None:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Temporary frame not defined.\n")
            exit(ec.RUNTIME_UNDEFINED_FRAME_ERROR)
        self.local_frame_stack.append(self.frames["TF"])
        self.frames["TF"] = None
        self.frames["LF"] = self.local_frame_stack[-1]

    def ins_pop_frame(self, ins):
        """
        Execute POPFRAME instruction
        """
        if len(self.local_frame_stack) == 0:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Local frame stack is empty.\n")
            exit(ec.RUNTIME_UNDEFINED_FRAME_ERROR)
        self.frames["TF"] = self.local_frame_stack.pop()
        if self.local_frame_stack:  # check if last local frame was popped
            self.frames["LF"] = self.local_frame_stack[-1]
        else:
            self.frames["LF"] = None

    def ins_defvar(self, ins):
        """
        Execute DEFVAR instruction
        """
        frame, variable_name = ins.arg1_value.split("@")

        if self.frames[frame] is None:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Frame {frame} not defined.\n")
            exit(ec.RUNTIME_UNDEFINED_FRAME_ERROR)
        if variable_name in self.frames[frame]:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Variable '{variable_name}' already exists in {frame}.\n")
            exit(ec.SEMANTIC_ERROR)

        self.frames[frame][variable_name] = (None, False)  # boolean value in tuple represents "defined"

    def ins_call(self, ins):
        """
        Execute CALL instruction
        """
        self.call_stack.append(self.i)
        self.i = self.labels[ins.arg1_value]

    def ins_return(self, ins):
        """
        Execute RETURN instruction
        """
        if self.call_stack:
            self.i = self.call_stack.pop()
        else:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Call stack is empty.\n")
            exit(ec.RUNTIME_MISSING_VALUE_ERROR)

    def ins_pushs(self, ins):
        """
        Execute PUSHS instruction
        """
        pushed_value = self.extract_value_from_symbol(ins, ins.arg1_type, ins.arg1_value)
        self.data_stack.append(pushed_value)

    def ins_pops(self, ins):
        """
        Execute POPS instruction
        """
        if self.data_stack:
            frame, var_name = ins.arg1_value.split("@")
            self.frames[frame][var_name] = self.data_stack.pop()
        else:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Data stack is empty.\n")
            exit(ec.RUNTIME_MISSING_VALUE_ERROR)

    def ins_math_or_logical_operation(self, ins):
        frame, var_name = ins.arg1_value.split("@")
        left_operand = self.extract_value_from_symbol(ins, ins.arg2_type, ins.arg2_value)
        right_operand = self.extract_value_from_symbol(ins, ins.arg3_type, ins.arg3_value)

        # data type control
        if ins.opcode in ["ADD", "SUB", "MUL", "IDIV"]:
            if not all(type(x) == int for x in [left_operand, right_operand]):
                sys.stderr.write(f"({ins.order}){ins.opcode}: All operands must be integers.\n")
                exit(ec.RUNTIME_WRONG_OPERAND_TYPE_ERROR)
        if ins.opcode in ["LT", "GT"]:
            if (None, True) in [left_operand, right_operand]:
                sys.stderr.write(f"({ins.order}){ins.opcode}: Cannot compare nil value.\n")
                exit(ec.RUNTIME_WRONG_OPERAND_TYPE_ERROR)
            if type(left_operand) != type(right_operand):
                sys.stderr.write(f"({ins.order}){ins.opcode}: Cannot compare values of different types.\n")
                exit(ec.RUNTIME_WRONG_OPERAND_TYPE_ERROR)
        if ins.opcode in ["AND", "OR"]:
            if not all(type(x) == bool for x in [left_operand, right_operand]):
                sys.stderr.write(f"({ins.order}){ins.opcode}: Values must be of bool type.\n")
                exit(ec.RUNTIME_WRONG_OPERAND_TYPE_ERROR)

        if ins.opcode == "ADD":
            result = left_operand + right_operand
        elif ins.opcode == "SUB":
            result = left_operand - right_operand
        elif ins.opcode == "MUL":
            result = left_operand * right_operand
        elif ins.opcode == "IDIV":
            if right_operand == 0:
                sys.stderr.write(f"({ins.order}){ins.opcode}: Division by zero.\n")
                exit(ec.RUNTIME_OPERAND_VALUE_ERROR)
            result = left_operand // right_operand
        elif ins.opcode == "LT":
            result = left_operand < right_operand
        elif ins.opcode == "GT":
            result = left_operand > right_operand
        elif ins.opcode == "EQ":
            if all(x == (None, True) for x in [left_operand, right_operand]):  # nil = nil
                result = True
            if any(x == (None, True) for x in [left_operand, right_operand]):  # nil != other data types
                result = False
            else:
                if type(left_operand) != type(right_operand):
                    sys.stderr.write(f"({ins.order}){ins.opcode}: Cannot compare values of different types.\n")
                    exit(ec.RUNTIME_WRONG_OPERAND_TYPE_ERROR)
                result = left_operand == right_operand
        elif ins.opcode == "AND":
            result = left_operand and right_operand
        elif ins.opcode == "OR":
            result = left_operand or right_operand

        self.frames[frame][var_name] = result

    def ins_not(self, ins):
        frame, var_name = ins.arg1_value.split("@")
        symbol_value = self.extract_value_from_symbol(ins, ins.arg2_type, ins.arg2_value)
        if type(symbol_value) != bool:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Value must be of bool type.\n")
            exit(ec.RUNTIME_WRONG_OPERAND_TYPE_ERROR)
        self.frames[frame][var_name] = not symbol_value

    def ins_int2char(self, ins):
        symb_value = self.extract_value_from_symbol(ins, ins.arg2_type, ins.arg2_value)
        frame, var_name = ins.arg1_value.split("@")

        try:
            self.frames[frame][var_name] = chr(symb_value)
        except TypeError:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Value must be integer.\n")
            exit(ec.RUNTIME_WRONG_OPERAND_TYPE_ERROR)
        except ValueError:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Value not in Unicode range.\n")
            exit(ec.RUNTIME_STRING_ERROR)

    def ins_stri2int(self, ins):
        frame, var_name = ins.arg1_value.split("@")
        left_operand = self.extract_value_from_symbol(ins, ins.arg2_type, ins.arg2_value)
        right_operand = self.extract_value_from_symbol(ins, ins.arg3_type, ins.arg3_value)

        if type(left_operand) != str or type(right_operand) != int:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Wrong value type.\n")
            exit(ec.RUNTIME_WRONG_OPERAND_TYPE_ERROR)

        try:
            self.frames[frame][var_name] = ord(left_operand[right_operand])
        except IndexError:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Index out of boundaries.\n")
            exit(ec.RUNTIME_STRING_ERROR)

    def ins_read(self, ins):
        frame, var_name = ins.arg1_value.split("@")

        if self.arguments.input:
            input_value = self.input_list.pop().strip()
        else:
            input_value = input()

        if ins.arg2_value == "string":
            result = input_value
        elif ins.arg2_value == "int":
            try:
                result = int(input_value)
            except ValueError:
                result = (None, False)
        elif ins.arg2_value == "bool":
            result = bool(re.match("^true$", input_value, re.IGNORECASE))
        else:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Unknown type.\n")
            exit(ec.XML_WRONG_STRUCTURE_ERROR)

        self.frames[frame][var_name] = result

    def ins_write(self, ins):
        """
        Execute WRITE instruction
        """
        if ins.arg1_type == "var":  # variable
            frame, var_name = ins.arg1_value.split("@")
            try:
                var_value = self.frames[frame][var_name]
            except KeyError:
                sys.stderr.write(f"({ins.order}){ins.opcode}: Unknown variable '{var_name}'.\n")
                exit(ec.RUNTIME_UNDEFINED_VARIABLE_ERROR)

            if type(var_value) is bool:
                print("true", end='') if var_value else print("false", end='')
            elif var_value == (None, True):
                pass  # print nothing
            elif var_value == (None, False):
                sys.stderr.write(f"({ins.order}){ins.opcode}: Variable '{var_name}' was declared but not defined.\n")
                exit(ec.RUNTIME_MISSING_VALUE_ERROR)
            else:
                print(var_value, end='')
        else:  # constant
            const_type, const_value = ins.arg1_type, ins.arg1_value
            if const_type in ["string", "int", "bool"]:
                print(const_value, end='')
            elif const_type == "nil":
                pass
            else:
                sys.stderr.write(f"({ins.order}){ins.opcode}: Unknown type '{ins.arg2_type}'.\n")
                exit(ec.SEMANTIC_ERROR)

    # todo more functions

    def ins_label(self, ins):
        """
        Do nothing (labels are handled before the interpretation)
        """
        pass

    def ins_jump(self, ins):
        """
        Execute JUMP instruction
        """
        if ins.arg1 not in self.labels:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Label not found.\n")
            exit(ec.SEMANTIC_ERROR)
        self.i = self.labels[ins.arg1] - 1

    def ins_exit(self, ins):
        if ins.arg1_type == "int" and 0 <= int(ins.arg1_value) <= 49:
            exit(int(ins.arg1_value))
        else:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Exit code not valid.\n")
            exit(ec.RUNTIME_OPERAND_VALUE_ERROR)


class Instruction:
    """
    Encapsulates information of the instruction.
    An instance should be created for each processed instruction.
    """

    def __init__(self, instruction_element):
        self.opcode = instruction_element.attrib['opcode']

        try:
            self.order = int(instruction_element.attrib['order'])
        except ValueError:
            sys.stderr.write("Order attribute value not valid\n")
            exit(ec.XML_WRONG_STRUCTURE_ERROR)

        # arguments are tuples (type, value)
        arg_element = instruction_element.find("arg1")
        if arg_element is not None:
            self.arg1_value = arg_element.text
            self.arg1_type = arg_element.attrib['type']
        else:
            self.arg1_value = None
            self.arg1_type = None

        arg_element = instruction_element.find("arg2")
        if arg_element is not None:
            self.arg2_value = arg_element.text
            self.arg2_type = arg_element.attrib['type']
        else:
            self.arg2_value = None
            self.arg2_type = None

        arg_element = instruction_element.find("arg3")
        if arg_element is not None:
            self.arg3_value = arg_element.text
            self.arg3_type = arg_element.attrib['type']
        else:
            self.arg3_value = None
            self.arg3_type = None

    # todo lex and syn control


interpret = Interpret()
interpret.create_instructions_array()
interpret.check_xml_structure()
interpret.search_labels()
interpret.execute()

# todo check double order and negative
