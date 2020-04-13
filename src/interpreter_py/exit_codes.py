# Author: Andrea Chimenti <xchime00>
# VUT FIT 2020
# IPP project

from enum import IntEnum


class ExitCodes(IntEnum):
    SUCCESS = 0
    ARGUMENT_ERROR = 10
    INPUT_FILE_ERROR = 11
    OUTPUT_FILE_ERROR = 12
    XML_NOT_WELL_FORMED_ERROR = 31
    XML_WRONG_STRUCTURE_ERROR = 32
    SEMANTIC_ERROR = 52
    RUNTIME_WRONG_OPERAND_TYPE_ERROR = 53
    RUNTIME_UNDEFINED_VARIABLE_ERROR = 54
    RUNTIME_UNDEFINED_FRAME_ERROR = 55
    RUNTIME_MISSING_VALUE_ERROR = 56
    RUNTIME_OPERAND_VALUE_ERROR = 57
    RUNTIME_STRING_ERROR = 58
    INTERNAL_ERROR = 99
