<?php

     // appliacation exit codes
     abstract class ExitCodesEnum
     {
         const Success = 0;
         const ArgumentError = 10;
         const InputFileError = 11;
         const OutputFileError = 12;
         const InvalidHeader = 21;
         const InvalidOpCode = 22;
         const LexicalOrSyntaxError = 23;
         const InternalError = 99;
     }

?>
