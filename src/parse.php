<?php

    require_once 'exitCodes.php';
    
    // parameters types of IPPcode20 instructions 
    abstract class ParamEnum
    {
        const Vari = 0;
        const Symb = 1;
        const Label = 2;
        const Type = 3;
    }
    
    class Parser
    {
        private $iia;
        // private $retrn_code; todo delete
        private $counter;
        private $xml_dom;

        // initiate variables
        public function __construct()
        {
            $this->iia = $this->create_instruction_info_array();
            $this->counter = 1;
            $this->xml_dom = new DOMDocument('1.0', 'UTF-8');
            $this->xml_dom->formatOutput = true;
            
        }

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
                    // $stats["com"]++; todo stats
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
                                    $param_regex = '~(LF|TF|GF)@([a-zA-Z_$&%!?*-])+~';
                                    break;
                                case ParamEnum::Symb:
                                    $param_regex = '~((LF|TF|GF)@([a-zA-Z_$&%!?*-])+)|((bool@(true|false))|nil@nil|int@([\d+-])+|string@([\S])*)~';
                                    break;
                                case ParamEnum::Label:
                                    $param_regex = '~([a-zA-Z_$&%!?*-])+~';
                                    break;
                                case ParamEnum::Type:
                                    $param_regex = '~(string|int|bool)~';
                                    break;
                                default:
                                    fwrite(STDERR, "Internal error\n");
                                    exit(ExitCodesEnum::InternalError);
                                    break;
                            }
                        
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
                                // echo $opcode . PHP_EOL . $line_words[$param_index] . PHP_EOL; // todo delete
                                fwrite(STDERR, "Too many parameters\n");
                                exit(ExitCodesEnum::LexicalOrSyntaxError);
                            }
                            // else todo stats
                            // {
                            //     $stats["com"]++;
                            // }
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

                                if (preg_match('~int@([\d+-])+~', $line_words[$i], $out)) // int
                                {
                                    $xml_arg->nodeValue = explode("@", $line_words[$i])[1]; // TODO control boundaries
                                    $xml_arg->setAttribute('type', 'int');

                                }
                                else if (preg_match('~string@([\S])*~', $line_words[$i], $out)) // string
                                {
                                    $xml_arg->nodeValue = explode("@", $line_words[$i])[1]; // TODO control boundaries + neprevadet escape sekvence
                                    $xml_arg->setAttribute('type', 'string');
                                }
                                else if (preg_match('~bool@(true|false)~', $line_words[$i], $out)) // bool
                                {
                                    $xml_arg->nodeValue = explode("@", strtolower($line_words[$i]))[1]; // TODO control boundaries
                                    $xml_arg->setAttribute('type', 'bool');
                                }
                                else if (preg_match('~nil@nil~', $line_words[$i], $out)) // nil
                                {
                                    $xml_arg->nodeValue = explode("@", $line_words[$i])[1]; // TODO control boundaries
                                    $xml_arg->setAttribute('type', 'nil');
                                }
                                else if (preg_match('~(LF|TF|GF)@([a-zA-Z_$&%!?*-])+~', $line_words[$i], $out)) // promenna
                                {
                                    $xml_arg->nodeValue = $line_words[$i];
                                    $xml_arg->setAttribute('type', 'var');
                                }
                                else if (preg_match('~(string|int|bool)~', $line_words[$i], $out)) // typ
                                {
                                    $xml_arg->nodeValue = $line_words[$i];
                                    $xml_arg->setAttribute('type', 'type');
                                }
                                else if (preg_match('~([a-zA-Z_$&%!?*-])+~', $line_words[$i], $out)) // navestri
                                {
                                    $xml_arg->nodeValue = $line_words[$i];
                                    $xml_arg->setAttribute('type', 'label');
                                }
                                else
                                {
                                    // echo $opcode . PHP_EOL . $line_words[$i] . PHP_EOL; // todo delete
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
                        // $stats["loc"]++; todo stats
                    }
                    else
                    {
                        fwrite(STDERR, "Not enough parameters\n");
                        exit(ExitCodesEnum::LexicalOrSyntaxError);
                    }

                    // label statistics
                    // if ("label" == $line_words[0]) todo stats
                    // {
                    //     if (!in_array($line_words[1], $labels))
                    //     {
                    //         array_push( $labels, $line_words[1]);
                    //         $stats["lab"]++;
                    //     }
                    // }

                    // if ("jump" == $line_words[0] || "jumpifeq" == $line_words[0] || "jumpifneq" == $line_words[0])
                    // {
                    //     $stats["jum"]++;
                    // }
                }
                // else if (preg_match('~#.*~', $line_words[0], $out)) // komentar todo delete
                // {
                //     echo "WTF TADY KOMENTAR?\n"; // todo delete
                // }
                // else if (empty($line_words[0])) // prazdny radek
                // {
                //     echo "prazdny radek\n";
                //     continue;
                // }
                else
                {
                    // echo $line; // todo delete
                    fwrite(STDERR, "Invalid opcode\n");
                    exit(ExitCodesEnum::InvalidOpCode);
                    // var_dump($line_words);
                    // echo "neznamy prikaz\n";
                    // exit(1); // todo delete
                }

                $this->counter++;
            }
            echo $this->xml_dom->saveXML();
            // echo "ahoj"; todo

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
                    // $stats["com"]++; todo stats
                    continue;
                }

                // header check
                return preg_match('~^(\s)*((.IPPcode20(\s)+#+)|(.IPPcode20)(\s)*$)~', $line, $out); // todo test
            }
        }

        // private function parse_instruction($line)
        // {

        // }

        static public function show_help()
        {
            echo "help" . PHP_EOL; // todo write help
        }

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
            $iia['add'] = [ParamEnum::Vari, ParamEnum::Symb, ParamEnum::Symb]; // todo musi byt int u +-*/
            $iia['sub'] = [ParamEnum::Vari, ParamEnum::Symb, ParamEnum::Symb]; // todo musi byt int u +-*/
            $iia['mul'] = [ParamEnum::Vari, ParamEnum::Symb, ParamEnum::Symb]; // todo musi byt int u +-*/
            $iia['idiv'] = [ParamEnum::Vari, ParamEnum::Symb, ParamEnum::Symb]; // todo musi byt int u +-*/
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

    // process --stats argument
    // $stats_enabled = false;
    // $stats = [
    //     "loc" => 0,
    //     "com" => 0,
    //     "lab" => 0,
    //     "jum" => 0];
    // if (array_key_exists("loc", $options) || array_key_exists("comments", $options) || array_key_exists("labels", $options) || array_key_exists("jumps", $options))
    // {
    //     if (array_key_exists("stats", $options))
    //     {
    //         $stats_enabled = true;
    //     }
    //     else 
    //     {
    //         fwrite(STDERR, "Missing stats argument\n");
    //         exit(ExitCodesEnum::ArgumentError);
    //     }
    // }
    

    /* MAIN FUNCTIONALITY */

    // $counter = 1;
    // $expecting_header = true;
    // $iia = create_instruction_info_array();
    // $labels = [];
    // $param_regex =
    // ['~(LF|TF|GF)@([a-zA-Z_$&%!?*-])+~', // var
    // '~((LF|TF|GF)@([a-zA-Z_$&%!?*-])+)|((bool@(true|false))|nil@nil|int@([\d+-])+|string@([\S])*)~', // symb
    // '~([a-zA-Z_$&%!?*-])+~', // label
    // '~(string|int|bool)~']; // type

    // $xml = new SimpleXMLElement('<xml/>'); delete
    

    // prochazeni souboru radek po radku
    

    // Header('Content-type: text/xml');
    // print($xml->asXML()); delete
    // echo $xml_dom->saveXML();

    // TODO UTF-8 kodovani
    // TODO check regexes

?>
