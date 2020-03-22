import xml.etree.ElementTree as ET
import argparse
import sys
import re
from exit_codes import ExitCodes as ec
import custom_exceptions

class Interpret:

    def __init__(self):
        self.arguments = self.process_arguments()
        xml_string = self.process_xml_source()
        self.root = ET.fromstring(xml_string)

    def process_xml_source(self):
        """
        Read xml source file or stdin, based on arguments given to the script
        Returns a string representation of the xml
        """
        if self.arguments.source:
            try:
                with open(self.arguments.source, 'r') as source:
                    xml_string = source.read()
            except:
                sys.stderr.write("Could not open source file.")
                raise InputFileError
        else:
            xml_string = sys.stdin.read()
        return xml_string

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

    def check_root_element(self):
        if not re.match("^program$", self.root.tag, re.I):
            raise custom_exceptions.XmlWrongStructureError

        if len(self.root.attrib) != 1:
            raise custom_exceptions.XmlWrongStructureError

        "language" in self.root.attrib and re.match("^ippcode20$", self.root.attrib["language"], re.I)

    def execute(self):
        print("Executing")
        print(self.root.tag)
        print(type(self.root.attrib))


interpret = Interpret()
interpret.check_xml_structure()
interpret.execute()

# print(interpret.__dict__)

# source and input cannot be the same
# if arguments.source == arguments.input:
#     exit(ec.ARGUMENT_ERROR)

# # load xml


# print(arguments)

# print(xml_string)

# tree = ET.parse(arguments.source)

# print(tree)
# root = tree.getroot()

# print(root)

# print(root.tag)
# print(root.attrib)


# for child in root:
#     print(child.attrib)
