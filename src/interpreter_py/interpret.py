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
        self.check_root_element()
        # todo check other stuff

    def check_root_element(self):
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
        for element in self.root:
            print(element.attrib)
            pass


        print("--------END--------")


interpret = Interpret()
interpret.check_xml_structure()
interpret.execute()
