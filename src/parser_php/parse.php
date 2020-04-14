<?php

    /**
     * Author: Andrea Chimenti <xchime00>
     * VUT FIT 2020
     * IPP project
    */

    require_once 'exitCodes.php';
    
    // types of IPPcode20 instruction parameters
    abstract class ParamEnum
    {
        const Vari = 0;
        const Symb = 1;
        const Label = 2;
        const Type = 3;
    }
    
    class Parser
    {
        private $iia; // instruction info array
        private $counter; // instruction counter
        private $xml_dom;

        // initiate variables
        public function __construct()
        {
            $this->iia = $this->create_instruction_info_array();
            $this->counter = 1;
            $this->xml_dom = new DOMDocument('1.0', 'UTF-8');
            $this->xml_dom->formatOutput = true;
        }

        // generate and print xml representation of IPPcode20 on stdout
        public function generate_xml()
        {
            $xml_progam = $this->xml_dom->createElement("program");
            $xml_progam->setAttribute('language', 'IPPcode20');
            $xml_progam = $this->xml_dom->appendChild($xml_progam);

            // check header
            if (!$this->header_ok())
            {
                fwrite(STDERR, "Missing header\n");
                exit(ExitCodesEnum::InvalidHeader);
            }

            // generate xml
            while($line = fgets(STDIN))
            {
                // modify processed line
                $line = trim($line);
                $line = preg_replace('~[\t\n]~', " ", $line); // delete tabs and newlines
                $line = preg_replace('~\s{2,}~', " ", $line); // delete consecutive spaces

                $line_words = explode(" ", $line);

                // skip empty line or comment
                if (count($line_words) == 1 && empty($line_words[0]))
                {
                    continue;
                }
                else if (preg_match('~#.*~', $line_words[0], $out))
                {
                    continue;
                }

                $opcode = strtolower($line_words[0]);
                if (array_key_exists($opcode, $this->iia)) // check if opcode is valid
                {
                    if (count($line_words) > count($this->iia[$opcode])) // check if instuction has enough parameters
                    {
                        $param_index = 1;
                        foreach ($this->iia[$opcode] as $expected_param) // check if instruction parameters are of valid type
                        {
                            switch ($expected_param)
                            {
                                case ParamEnum::Vari:
                                    $param_regex = '~(LF|TF|GF)@[a-zA-Z_$&%!?*-][a-zA-Z0-9_$&%!?*-]*(\s|$|#)~';
                                    break;
                                case ParamEnum::Symb:
                                    $param_regex = '~((LF|TF|GF)@[a-zA-Z_$&%!?*-][a-zA-Z0-9_$&%!?*-]*(\s|$|#))|((bool@(true|false)(\s|$|#))|nil@nil(\s|$|#)|int@([\d+-])+(\s|$|#)|string@([\S])*(\s|$|#))~';
                                    break;
                                case ParamEnum::Label:
                                    $param_regex = '~(\s|^)[a-zA-Z_$&%!?*-][a-zA-Z0-9_$&%!?*-]*(\s|$|#)~';
                                    break;
                                case ParamEnum::Type:
                                    $param_regex = '~(string|int|bool)(\s|$|#)~';
                                    break;
                                default:
                                    fwrite(STDERR, "Internal error\n");
                                    exit(ExitCodesEnum::InternalError);
                                    break;
                            }
                        
                            // compare instruction parameter with appropriate regex
                            if (!preg_match($param_regex, $line_words[$param_index], $out))
                            {
                                fwrite(STDERR, "Expected parameter not valid\n");
                                exit(ExitCodesEnum::LexicalOrSyntaxError);
                            }
                            $param_index++;
                        }

                        if (array_key_exists($param_index, $line_words)) // check if there is a comment or nothing after parameters
                        {
                            if (!preg_match('~#.*~', $line_words[$param_index], $out))
                            {
                                fwrite(STDERR, "Too many parameters\n");
                                exit(ExitCodesEnum::LexicalOrSyntaxError);
                            }
                        }

                        // create instruction element
                        $xml_instruction = $this->xml_dom->createElement('instruction');
                        $xml_instruction->setAttribute('order', strval($this->counter));
                        $xml_instruction->setAttribute('opcode', strval(strtoupper($opcode)));


                        // createg tag elements
                        for ($i = 1; $i <= count($this->iia[$opcode]); $i++)
                        {
                            if (array_key_exists($i, $line_words))
                            {
                                $xml_arg = $this->xml_dom->createElement('arg' . $i);

                                if (preg_match('~int@([\d+-])+(\s|$|#)~', $line_words[$i], $out)) // int
                                {
                                    $xml_arg->nodeValue = explode("@", $line_words[$i])[1];
                                    $xml_arg->setAttribute('type', 'int');

                                }
                                else if (preg_match('~string@([\S])*(\s|$|#)~', $line_words[$i], $out)) // string
                                {
                                    $xml_arg->nodeValue = explode("@", $line_words[$i])[1];
                                    $xml_arg->setAttribute('type', 'string');
                                }
                                else if (preg_match('~bool@(true|false)(\s|$|#)~', $line_words[$i], $out)) // bool
                                {
                                    $xml_arg->nodeValue = explode("@", strtolower($line_words[$i]))[1];
                                    $xml_arg->setAttribute('type', 'bool');
                                }
                                else if (preg_match('~nil@nil(\s|$|#)~', $line_words[$i], $out)) // nil
                                {
                                    $xml_arg->nodeValue = explode("@", $line_words[$i])[1];
                                    $xml_arg->setAttribute('type', 'nil');
                                }
                                else if (preg_match('~(LF|TF|GF)@[a-zA-Z_$&%!?*-][a-zA-Z0-9_$&%!?*-]*(\s|$|#)~', $line_words[$i], $out)) // variable
                                {
                                    $xml_arg->nodeValue = htmlspecialchars($line_words[$i]);
                                    $xml_arg->setAttribute('type', 'var');
                                }
                                else if (preg_match('~(string|int|bool)(\s|$|#)~', $line_words[$i], $out)) // type
                                {
                                    $xml_arg->nodeValue = $line_words[$i];
                                    $xml_arg->setAttribute('type', 'type');
                                }
                                else if (preg_match('~(\s|^)[a-zA-Z_$&%!?*-][a-zA-Z0-9_$&%!?*-]*(\s|$|#)~', $line_words[$i], $out)) // label
                                {
                                    $xml_arg->nodeValue = $line_words[$i];
                                    $xml_arg->setAttribute('type', 'label');
                                }
                                else
                                {
                                    fwrite(STDERR, "Found unknown parameter\n");
                                    exit(ExitCodesEnum::LexicalOrSyntaxError);
                                }
                                
                                $xml_instruction->appendChild($xml_arg);
                            }
                            else
                            {
                                break;
                            }
                        }
                        
                        $xml_progam->appendChild($xml_instruction);
                    }
                    else // instruction has not enough parameters
                    {
                        fwrite(STDERR, "Not enough parameters\n");
                        exit(ExitCodesEnum::LexicalOrSyntaxError);
                    }
                }
                else
                {
                    fwrite(STDERR, "Invalid opcode\n");
                    exit(ExitCodesEnum::InvalidOpCode);
                }

                $this->counter++;
            }

            // print generated xml on stdout
            echo $this->xml_dom->saveXML();
        }

        // returns true if header is found, otherwise false
        private function header_ok()
        {
            while($line = fgets(STDIN))
            {
                // modify processed line
                $line = trim($line);
                $line = preg_replace('~[\t\n]~', " ", $line); // delete tabs and newlines
                $line = preg_replace('~\s{2,}~', " ", $line); // delete consecutive spaces

                $line_words = explode(" ", $line);

                // skip empty line or comment
                if (count($line_words) == 1 && empty($line_words[0]))
                {
                    continue;
                }
                else if (preg_match('~#.*~', $line_words[0], $out))
                {
                    continue;
                }
                // header check
                return preg_match('~^(\s)*((.IPPcode20(\s)+#+)|(.IPPcode20)(\s)*$)~i', $line, $out);
            }
            echo $this->xml_dom->saveXML();
            exit(ExitCodesEnum::Success); // end the program success in case of blank file on input
        }

        // print program help on stdin
        static public function show_help()
        {
            echo "Parse.php is a simple script which expects and reads IPPcode20 source code from stdin.\n";
            echo "The script then checks for lexical and syntactic errors in the source code and outputs an XML representation on stdout.\n";
        }

        // return an array which specifies what parameters (array values) do IPPcode20 instructions (array keys) expect
        private function create_instruction_info_array()
        {
            $iia = array(); // instruction info array

            $iia['move'] = [ParamEnum::Vari, ParamEnum::Symb];
            $iia['createframe'] = [];
            $iia['pushframe'] = [];
            $iia['popframe'] = [];
            $iia['defvar'] = [ParamEnum::Vari];
            $iia['call'] = [ParamEnum::Label];
            $iia['return'] = [];
            $iia['pushs'] = [ParamEnum::Symb];
            $iia['pops'] = [ParamEnum::Vari];
            $iia['add'] = [ParamEnum::Vari, ParamEnum::Symb, ParamEnum::Symb];
            $iia['sub'] = [ParamEnum::Vari, ParamEnum::Symb, ParamEnum::Symb];
            $iia['mul'] = [ParamEnum::Vari, ParamEnum::Symb, ParamEnum::Symb];
            $iia['idiv'] = [ParamEnum::Vari, ParamEnum::Symb, ParamEnum::Symb];
            $iia['lt'] = [ParamEnum::Vari, ParamEnum::Symb, ParamEnum::Symb];
            $iia['gt'] = [ParamEnum::Vari, ParamEnum::Symb, ParamEnum::Symb];
            $iia['eq'] = [ParamEnum::Vari, ParamEnum::Symb, ParamEnum::Symb];
            $iia['and'] = [ParamEnum::Vari, ParamEnum::Symb, ParamEnum::Symb];
            $iia['or'] = [ParamEnum::Vari, ParamEnum::Symb, ParamEnum::Symb];
            $iia['not'] = [ParamEnum::Vari, ParamEnum::Symb];
            $iia['int2char'] = [ParamEnum::Vari, ParamEnum::Symb];
            $iia['stri2int'] = [ParamEnum::Vari, ParamEnum::Symb, ParamEnum::Symb];
            $iia['read'] = [ParamEnum::Vari, ParamEnum::Type];
            $iia['write'] = [ParamEnum::Symb];
            $iia['concat'] = [ParamEnum::Vari, ParamEnum::Symb, ParamEnum::Symb];
            $iia['strlen'] = [ParamEnum::Vari, ParamEnum::Symb];
            $iia['getchar'] = [ParamEnum::Vari, ParamEnum::Symb, ParamEnum::Symb];
            $iia['setchar'] = [ParamEnum::Vari, ParamEnum::Symb, ParamEnum::Symb];
            $iia['type'] = [ParamEnum::Vari, ParamEnum::Symb];
            $iia['label'] = [ParamEnum::Label];
            $iia['jump'] = [ParamEnum::Label];
            $iia['jumpifeq'] = [ParamEnum::Label, ParamEnum::Symb, ParamEnum::Symb];
            $iia['jumpifneq'] = [ParamEnum::Label, ParamEnum::Symb, ParamEnum::Symb];
            $iia['exit'] = [ParamEnum::Symb];
            $iia['dprint'] = [ParamEnum::Symb];
            $iia['break'] = [];

            return $iia;
        }
    }

    /* COMAND LINE ARGUMENTS PROCESSING */

    $options = getopt("h", ["help", "stats:"]);
    
    // process --help argument
    if (array_key_exists("help", $options) || array_key_exists("h", $options))
    {
        if (count($options) == 1)
        {
            Parser::show_help();
            exit(ExitCodesEnum::Success);
        }
        else
        {
            fwrite(STDERR, "Help argument cannot be combined with other arguments\n");
            exit(ExitCodesEnum::ArgumentError);
        }
    }

    $parse = new Parser();
    $parse->generate_xml();

?>
