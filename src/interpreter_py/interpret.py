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

    def check_syntax(self):
        syntax_analyser = SyntaxAnalyser()

        order_values_list = [x.order for x in self.instructions]
        if len(order_values_list) != len(set(order_values_list)):
            sys.stderr.write(f"Duplicit order\n")
            exit(ec.XML_WRONG_STRUCTURE_ERROR)

        for ins in self.instructions:
            syntax_analyser.check_instruction(ins)

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

    def extract_value_from_symbol(self, ins, symbol_type, symbol_value, return_undefined=False):
        if symbol_type == "var":  # variable
            frame, variable_name = symbol_value.split("@")
            try:
                var_value = self.load_variable_value(ins, frame, variable_name)
                if var_value == (None, False):
                    if return_undefined:
                        return (None, False)
                    else:
                        sys.stderr.write(f"({ins.order}){ins.opcode}: Undefined variable '{variable_name}'.\n")
                        exit(ec.RUNTIME_MISSING_VALUE_ERROR)
            except KeyError:
                sys.stderr.write(f"({ins.order}){ins.opcode}: Unknown variable '{variable_name}'.\n")
                exit(ec.RUNTIME_UNDEFINED_VARIABLE_ERROR)
            return var_value
        elif symbol_type == "string":
            for x in list(range(99)):
                symbol_value = symbol_value.replace("\\0" + str(x).zfill(2), chr(x))
            return symbol_value
        if symbol_type == "int":
            return int(symbol_value)
        if symbol_type == "bool":
            return True if symbol_value.lower() == "true" else False
        elif symbol_type == "nil":
            return (None, True)
        else:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Unknown type '{symbol_type}'.\n")
            exit(ec.SEMANTIC_ERROR)

    def execute(self):
        """
        Run interpretation.
        """
        self.i = 0
        while self.i < len(self.instructions):
            instruction = self.instructions[self.i]
            instruction_handler = self.instruction_swticher(instruction.opcode)
            instruction_handler(instruction)
            self.i += 1

    def create_instructions_array(self):
        for element in self.root:
            if element.tag != "instruction":
                sys.stderr.write(f"Unknown element.\n")
                exit(ec.XML_WRONG_STRUCTURE_ERROR)
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
        elif opcode in ["ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR", "CONCAT"]:
            return self.ins_math_or_logical_operation
        elif opcode == "NOT":
            return self.ins_not
        elif opcode == "INT2CHAR":
            return self.ins_int2char
        elif opcode in ["STRI2INT", "GETCHAR"]:
            return self.ins_stri2int_getchar
        elif opcode == "READ":
            return self.ins_read
        elif opcode == "WRITE":
            return self.ins_write
        elif opcode == "STRLEN":
            return self.ins_strlen
        elif opcode == "SETCHAR":
            return self.ins_setchar
        elif opcode == "TYPE":
            return self.ins_type
        elif opcode == "LABEL":
            return self.ins_label
        elif opcode == "JUMP":
            return self.ins_jump
        elif opcode in ["JUMPIFEQ", "JUMPIFNEQ"]:
            return self.ins_jump_on_condition
        elif opcode == "EXIT":
            return self.ins_exit
        elif opcode == "DPRINT":
            return self.ins_dprint
        elif opcode == "BREAK":
            return self.ins_break
        else:
            sys.stderr.write(f"Opcode {opcode} not valid\n")
            exit(ec.XML_WRONG_STRUCTURE_ERROR)

    def store_variable_value(self, ins, frame, var_name, value):
        try:
            if var_name in self.frames[frame]:
                self.frames[frame][var_name] = value
            else:
                sys.stderr.write(f"({ins.order}){ins.opcode}: Undefined variable '{var_name}'.\n")
                exit(ec.RUNTIME_UNDEFINED_VARIABLE_ERROR)
        except TypeError:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Frame '{frame}' not initialized.\n")
            exit(ec.RUNTIME_UNDEFINED_FRAME_ERROR)
        except KeyError:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Unknown variable '{var_name}'.\n")
            exit(ec.RUNTIME_UNDEFINED_VARIABLE_ERROR)

    def load_variable_value(self, ins, frame, var_name):
        try:
            return self.frames[frame][var_name]
        except TypeError:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Frame '{frame}' not initialized.\n")
            exit(ec.RUNTIME_UNDEFINED_FRAME_ERROR)
        except KeyError:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Unknown variable '{var_name}'.\n")
            exit(ec.RUNTIME_UNDEFINED_VARIABLE_ERROR)    

    # functions for instuction handling

    def ins_move(self, ins):
        """
        Execute MOVE instruction
        """
        dst_frame, dst_var_name = ins.arg1_value.split("@")
        new_value = self.extract_value_from_symbol(ins, ins.arg2_type, ins.arg2_value)
        self.store_variable_value(ins, dst_frame, dst_var_name, new_value)

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
        if ins.arg1_value in self.labels:
            self.call_stack.append(self.i)
            self.i = self.labels[ins.arg1_value]
        else:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Label '{ins.arg1_value}' not found.\n")
            exit(ec.SEMANTIC_ERROR)

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
            popped_value = self.data_stack.pop()
            self.store_variable_value(ins, frame, var_name, popped_value)
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
        if ins.opcode == "CONCAT":
            if not all(type(x) == str for x in [left_operand, right_operand]):
                sys.stderr.write(f"({ins.order}){ins.opcode}: Values must be of string type.\n")
                exit(ec.RUNTIME_WRONG_OPERAND_TYPE_ERROR)

        if ins.opcode in ["ADD", "CONCAT"]:
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
            elif any(x == (None, True) for x in [left_operand, right_operand]):  # nil != other data types
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

        self.store_variable_value(ins, frame, var_name, result)

    def ins_not(self, ins):
        frame, var_name = ins.arg1_value.split("@")
        symbol_value = self.extract_value_from_symbol(ins, ins.arg2_type, ins.arg2_value)
        if type(symbol_value) != bool:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Value must be of bool type.\n")
            exit(ec.RUNTIME_WRONG_OPERAND_TYPE_ERROR)

        self.store_variable_value(ins, frame, var_name, not symbol_value)

    def ins_int2char(self, ins):
        symb_value = self.extract_value_from_symbol(ins, ins.arg2_type, ins.arg2_value)
        frame, var_name = ins.arg1_value.split("@")

        if type(symb_value) != int:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Value must be integer.\n")
            exit(ec.RUNTIME_WRONG_OPERAND_TYPE_ERROR)

        try:
            result = chr(symb_value)
        except ValueError:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Value not in Unicode range.\n")
            exit(ec.RUNTIME_STRING_ERROR)

        self.store_variable_value(ins, frame, var_name, result)

    def ins_stri2int_getchar(self, ins):
        frame, var_name = ins.arg1_value.split("@")
        left_operand = self.extract_value_from_symbol(ins, ins.arg2_type, ins.arg2_value)
        right_operand = self.extract_value_from_symbol(ins, ins.arg3_type, ins.arg3_value)

        if type(left_operand) != str or type(right_operand) != int:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Wrong value type.\n")
            exit(ec.RUNTIME_WRONG_OPERAND_TYPE_ERROR)

        if right_operand < 0:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Index out of boundaries.\n")
            exit(ec.RUNTIME_STRING_ERROR)

        try:
            if ins.opcode == "STRI2INT":
                result = ord(left_operand[right_operand])
            else:
                result = left_operand[right_operand]
        except IndexError:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Index out of boundaries.\n")
            exit(ec.RUNTIME_STRING_ERROR)

        self.store_variable_value(ins, frame, var_name, result)

    def ins_read(self, ins):
        frame, var_name = ins.arg1_value.split("@")

        if self.arguments.input:
            if len(self.input_list) == 0:
                self.store_variable_value(ins, frame, var_name, (None, True))
                return
            else:
                input_value = self.input_list.pop().strip()
        else:
            try:
                input_value = input()
            except EOFError:
                self.store_variable_value(ins, frame, var_name, (None, True))
                return

        if ins.arg2_value == "string":
            result = input_value
        elif ins.arg2_value == "int":
            try:
                result = int(input_value)
            except ValueError:
                result = (None, True)
        elif ins.arg2_value == "bool":
            result = bool(re.match("^true$", input_value, re.IGNORECASE))
        else:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Unknown type.\n")
            exit(ec.XML_WRONG_STRUCTURE_ERROR)

        self.store_variable_value(ins, frame, var_name, result)

    def ins_write(self, ins):
        """
        Execute WRITE instruction
        """
        if ins.arg1_type == "var":  # variable
            frame, var_name = ins.arg1_value.split("@")
            var_value = self.load_variable_value(ins, frame, var_name)

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
            if const_type in ["int", "bool"]:
                print(const_value, end='')
            elif const_type == "string":
                for x in list(range(33)) + [35, 92]:
                    const_value = const_value.replace("\\0" + str(x).zfill(2), chr(x))
                print(const_value, end='')
            elif const_type == "nil":
                pass
            else:
                sys.stderr.write(f"({ins.order}){ins.opcode}: Unknown type '{ins.arg2_type}'.\n")
                exit(ec.SEMANTIC_ERROR)

    def ins_strlen(self, ins):
        frame, var_name = ins.arg1_value.split("@")
        symbol_value = self.extract_value_from_symbol(ins, ins.arg2_type, ins.arg2_value)

        if type(symbol_value) != str:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Operand must be string.\n")
            exit(ec.RUNTIME_WRONG_OPERAND_TYPE_ERROR)

        self.store_variable_value(ins, frame, var_name, len(symbol_value))

    def ins_setchar(self, ins):
        frame, var_name = ins.arg1_value.split("@")
        left_operand = self.extract_value_from_symbol(ins, ins.arg2_type, ins.arg2_value)
        right_operand = self.extract_value_from_symbol(ins, ins.arg3_type, ins.arg3_value)

        if type(left_operand) != int or type(right_operand) != str:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Wrong operand type.\n")
            exit(ec.RUNTIME_WRONG_OPERAND_TYPE_ERROR)

        old_value = self.load_variable_value(ins, frame, var_name)
        if old_value == (None, False):
            sys.stderr.write(f"({ins.order}){ins.opcode}: Wrong operand type.\n")
            exit(ec.RUNTIME_MISSING_VALUE_ERROR)
        if type(old_value) != str:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Wrong operand type.\n")
            exit(ec.RUNTIME_WRONG_OPERAND_TYPE_ERROR)
        old_value = str(old_value)

        if left_operand < 0 or left_operand >= len(old_value):
            sys.stderr.write(f"({ins.order}){ins.opcode}: Ivalid string.\n")
            exit(ec.RUNTIME_STRING_ERROR)

        try:
            new_value = old_value[0:left_operand] + right_operand[0] + old_value[left_operand + 1:]
            self.store_variable_value(ins, frame, var_name, new_value)
        except IndexError:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Ivalid string.\n")
            exit(ec.RUNTIME_STRING_ERROR)

    def ins_type(self, ins):
        frame, var_name = ins.arg1_value.split("@")
        symbol_value = self.extract_value_from_symbol(ins, ins.arg2_type, ins.arg2_value, return_undefined=True)

        if type(symbol_value) == str:
            self.store_variable_value(ins, frame, var_name, "string")
        elif type(symbol_value) == int:
            self.store_variable_value(ins, frame, var_name, "int")
        elif type(symbol_value) == bool:
            self.store_variable_value(ins, frame, var_name, "bool")
        elif symbol_value == (None, True):
            self.store_variable_value(ins, frame, var_name, "nil")
        else:
            self.store_variable_value(ins, frame, var_name, "")

    def ins_label(self, ins):
        """
        Do nothing (labels are handled before the interpretation)
        """
        pass

    def ins_jump(self, ins):
        """
        Execute JUMP instruction
        """
        if ins.arg1_value not in self.labels:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Label not found.\n")
            exit(ec.SEMANTIC_ERROR)
        self.i = self.labels[ins.arg1_value] - 1

    def ins_jump_on_condition(self, ins):
        """
        Execute JUMPIFEQ and JUMPIFNEQ instructions
        """
        if ins.arg1_value not in self.labels:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Label not found.\n")
            exit(ec.SEMANTIC_ERROR)
        left_operand = self.extract_value_from_symbol(ins, ins.arg2_type, ins.arg2_value)
        right_operand = self.extract_value_from_symbol(ins, ins.arg3_type, ins.arg3_value)

        if left_operand == right_operand == (None, True):
            equality = True
        elif (None, True) in [left_operand, right_operand]:
            equality = False
        elif type(left_operand) == type(right_operand):
            equality = left_operand == right_operand
        else:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Wrong value type.\n")
            exit(ec.RUNTIME_WRONG_OPERAND_TYPE_ERROR)

        if (ins.opcode == "JUMPIFEQ"):
            if equality:
                self.i = self.labels[ins.arg1_value] - 1
        else:  # JUMPIFNEQ
            if not equality:
                self.i = self.labels[ins.arg1_value] - 1

    def ins_exit(self, ins):
        exit_code = self.extract_value_from_symbol(ins, ins.arg1_type, ins.arg1_value)

        if type(exit_code) != int:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Exit code not valid.\n")
            exit(ec.RUNTIME_WRONG_OPERAND_TYPE_ERROR)

        if 0 <= exit_code <= 49:
            exit(exit_code)
        else:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Exit code not valid.\n")
            exit(ec.RUNTIME_OPERAND_VALUE_ERROR)

    def ins_dprint(self, ins):
        symbol_value = self.extract_value_from_symbol(ins, ins.arg1_type, ins.arg1_value)
        sys.stderr.write(str(symbol_value))

    def ins_break(self, ins):
        sys.stderr.write(f"Inner instruction counter: {self.i}\n")
        sys.stderr.write(f"Total local frames: {len(self.local_frame_stack)}\n")
        sys.stderr.write(f"Data stack: {self.data_stack}\n")
        sys.stderr.write(f"GF: {self.frames['GF']}\n")
        sys.stderr.write(f"LF: {self.frames['LF']}\n")
        sys.stderr.write(f"TF: {self.frames['TF']}\n")


class Instruction:
    """
    Encapsulates information of the instruction.
    An instance should be created for each processed instruction.
    """

    def __init__(self, instruction_element):
        if 'opcode' in instruction_element.attrib:
            self.opcode = instruction_element.attrib['opcode'].upper()
        else:
            sys.stderr.write("Non existent opcode\n")
            exit(ec.XML_WRONG_STRUCTURE_ERROR)

        try:
            self.order = int(instruction_element.attrib['order'])
        except ValueError:
            sys.stderr.write("Order attribute value not valid\n")
            exit(ec.XML_WRONG_STRUCTURE_ERROR)
        except KeyError:
            sys.stderr.write("Non existent order\n")
            exit(ec.XML_WRONG_STRUCTURE_ERROR)

        if self.order < 1:
            sys.stderr.write("Negative order\n")
            exit(ec.XML_WRONG_STRUCTURE_ERROR)

        arg_element = instruction_element.find("arg1")
        if arg_element is not None:
            if arg_element.attrib['type'] == "string" and arg_element.text is None:
                self.arg1_value = ""
            else:
                self.arg1_value = arg_element.text
            self.arg1_type = arg_element.attrib['type']
        else:
            self.arg1_value = None
            self.arg1_type = None

        arg_element = instruction_element.find("arg2")
        if arg_element is not None:
            if arg_element.attrib['type'] == "string" and arg_element.text is None:
                self.arg2_value = ""
            else:
                self.arg2_value = arg_element.text
            self.arg2_type = arg_element.attrib['type']
        else:
            self.arg2_value = None
            self.arg2_type = None

        arg_element = instruction_element.find("arg3")
        if arg_element is not None:
            if arg_element.attrib['type'] == "string" and arg_element.text is None:
                self.arg3_value = ""
            else:
                self.arg3_value = arg_element.text
            self.arg3_type = arg_element.attrib['type']
        else:
            self.arg3_value = None
            self.arg3_type = None


class SyntaxAnalyser:

    def __init__(self):
        self.expected_types = dict()
        self.expected_types["MOVE"] = ["var", "sym"]
        self.expected_types["CREATEFRAME"] = []
        self.expected_types["PUSHFRAME"] = []
        self.expected_types["POPFRAME"] = []
        self.expected_types["DEFVAR"] = ["var"]
        self.expected_types["CALL"] = ["lab"]
        self.expected_types["RETURN"] = []
        self.expected_types["PUSHS"] = ["sym"]
        self.expected_types["POPS"] = ["var"]
        self.expected_types["ADD"] = ["var", "sym", "sym"]
        self.expected_types["SUB"] = ["var", "sym", "sym"]
        self.expected_types["MUL"] = ["var", "sym", "sym"]
        self.expected_types["IDIV"] = ["var", "sym", "sym"]
        self.expected_types["LT"] = ["var", "sym", "sym"]
        self.expected_types["GT"] = ["var", "sym", "sym"]
        self.expected_types["EQ"] = ["var", "sym", "sym"]
        self.expected_types["AND"] = ["var", "sym", "sym"]
        self.expected_types["OR"] = ["var", "sym", "sym"]
        self.expected_types["NOT"] = ["var", "sym"]
        self.expected_types["INT2CHAR"] = ["var", "sym"]
        self.expected_types["STRI2INT"] = ["var", "sym", "sym"]
        self.expected_types["READ"] = ["var", "typ"]
        self.expected_types["WRITE"] = ["sym"]
        self.expected_types["CONCAT"] = ["var", "sym", "sym"]
        self.expected_types["STRLEN"] = ["var", "sym"]
        self.expected_types["GETCHAR"] = ["var", "sym", "sym"]
        self.expected_types["SETCHAR"] = ["var", "sym", "sym"]
        self.expected_types["TYPE"] = ["var", "sym"]
        self.expected_types["LABEL"] = ["lab"]
        self.expected_types["JUMP"] = ["lab"]
        self.expected_types["JUMPIFEQ"] = ["lab", "sym", "sym"]
        self.expected_types["JUMPIFNEQ"] = ["lab", "sym", "sym"]
        self.expected_types["EXIT"] = ["sym"]
        self.expected_types["DPRINT"] = ["sym"]
        self.expected_types["BREAK"] = []

        # append missing None values so that each element is a list of 3 values
        for key, value in self.expected_types.items():
            none_to_be_appended = 3 - len(value)
            for i in range(none_to_be_appended):
                value.append(None)

    def check_instruction(self, ins):
        if ins.opcode not in self.expected_types:
            sys.stderr.write(f"({ins.order}){ins.opcode}: Unknown instruction.\n")
            exit(ec.XML_WRONG_STRUCTURE_ERROR)

        for i, expected_type in enumerate(self.expected_types[ins.opcode]):
            if i == 0:
                arg_val = ins.arg1_value
                arg_type = ins.arg1_type
            elif i == 1:
                arg_val = ins.arg2_value
                arg_type = ins.arg2_type
            else:
                arg_val = ins.arg3_value
                arg_type = ins.arg3_type

            if expected_type == "var":
                if arg_type != "var" or not re.match('^(GF|LF|TF)@[a-zA-Z_\-$&%*!?][a-zA-Z0-9_\-$&%*!?]*$', arg_val):
                    sys.stderr.write(f"({ins.order}){ins.opcode}: Argument error.\n")
                    exit(ec.XML_WRONG_STRUCTURE_ERROR)

            elif expected_type == "sym":
                if arg_type == "var":
                    if not re.match('^(GF|LF|TF)@[a-zA-Z_\-$&%*!?][a-zA-Z0-9_\-$&%*!?]*$', arg_val):
                        sys.stderr.write(f"({ins.order}){ins.opcode}: Argument error.\n")
                        exit(ec.XML_WRONG_STRUCTURE_ERROR)
                elif arg_type == "string":
                    if not re.match('^\S*$', arg_val) or "#" in arg_val:
                        sys.stderr.write(f"({ins.order}){ins.opcode}: Argument error.\n")
                        exit(ec.XML_WRONG_STRUCTURE_ERROR)
                elif arg_type == "int":
                    if not re.match('^([\-]?[1-9][0-9]*|[\-]?0)$', arg_val):
                        sys.stderr.write(f"({ins.order}){ins.opcode}: Argument error.\n")
                        exit(ec.XML_WRONG_STRUCTURE_ERROR)
                elif arg_type == "bool":
                    if not re.match('^(true|false)$', arg_val, re.IGNORECASE):
                        sys.stderr.write(f"({ins.order}){ins.opcode}: Argument error.\n")
                        exit(ec.XML_WRONG_STRUCTURE_ERROR)
                elif arg_type == "nil":
                    if not re.match('^nil$', arg_val, re.IGNORECASE):
                        sys.stderr.write(f"({ins.order}){ins.opcode}: Argument error.\n")
                        exit(ec.XML_WRONG_STRUCTURE_ERROR)
                else:
                    sys.stderr.write(f"({ins.order}){ins.opcode}: Argument error.\n")
                    exit(ec.XML_WRONG_STRUCTURE_ERROR)
                pass
            elif expected_type == "lab":
                if arg_type != "label" or not re.match('^[a-zA-Z_\-$&%*!?][a-zA-Z0-9_\-$&%*!?]*$', arg_val):
                    sys.stderr.write(f"({ins.order}){ins.opcode}: Argument error.\n")
                    exit(ec.XML_WRONG_STRUCTURE_ERROR)
            elif expected_type == "typ":
                if arg_type != "type" or not re.match('^(int|string|bool)$', arg_val):
                    sys.stderr.write(f"({ins.order}){ins.opcode}: Argument error.\n")
                    exit(ec.XML_WRONG_STRUCTURE_ERROR)
            else:  # no value expected
                if arg_val is not None or arg_type is not None:
                    sys.stderr.write(f"({ins.order}){ins.opcode}: Too many arguments.\n")
                    exit(ec.XML_WRONG_STRUCTURE_ERROR)


interpret = Interpret()
interpret.check_xml_structure()
interpret.create_instructions_array()
interpret.check_syntax()
interpret.search_labels()
interpret.execute()

# todo check double order and negative
# duplicit argument
# test bool TRuE
# pristup to ramcu