<?php

    // parameters types of IPPcode20 instructions 
    abstract class ParamEnum
    {
        const Vari = 0;
        const Symb = 1;
        const Label = 2;
        const Type = 3;
    }

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

    function create_instruction_info_array()
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

    /* COMAND LINE ARGUMENTS PROCESSING */

    $options = getopt("h", ["help", "stats:"]);
    
    // process --help argument
    if (array_key_exists("help", $options) || array_key_exists("h", $options))
    {
        if (count($options) == 1)
        {
            echo "napoveda\n"; // TODO finish help
            exit(ExitCodesEnum::Success);
        }
        else
        {
            fwrite(STDERR, "Help argument cannot be combined with other arguments\n");
            exit(ExitCodesEnum::ArgumentError);
        }
    }

    // process --stats argument
    $stats_enabled = false;
    $stats = [
        "loc" => 0,
        "com" => 0,
        "lab" => 0,
        "jum" => 0];
    if (array_key_exists("loc", $options) || array_key_exists("comments", $options) || array_key_exists("labels", $options) || array_key_exists("jumps", $options))
    {
        if (array_key_exists("stats", $options))
        {
            $stats_enabled = true;
        }
        else 
        {
            fwrite(STDERR, "Missing stats argument\n");
            exit(ExitCodesEnum::ArgumentError);
        }
    }
    

    /* MAIN FUNCTIONALITY */

    $counter = 1;
    $expecting_header = true;
    $iia = create_instruction_info_array();
    $labels = [];
    $param_regex =
    ['~(LF|TF|GF)@([a-zA-Z_$&%!?*-])+~', // var
    '~((LF|TF|GF)@([a-zA-Z_$&%!?*-])+)|((bool@(true|false))|nil@nil|int@([\d+-])+|string@([\S])*)~', // symb
    '~([a-zA-Z_$&%!?*-])+~', // label
    '~(string|int|bool)~']; // type

    // $xml = new SimpleXMLElement('<xml/>'); delete
    $xml_dom = new DOMDocument('1.0', 'UTF-8');
    $xml_dom->formatOutput = true;
    $xml_progam = $xml_dom->createElement("program");
    $xml_progam->setAttribute('language', 'IPPcode20');
    $xml_progam = $xml_dom->appendChild($xml_progam);

    // prochazeni souboru radek po radku
    while($line = fgets(STDIN))
    {
        // uprava prave zpracovavaneho radku
        $line = trim($line);
        $line = preg_replace('~[\t\n]~', " ", $line); // odstraneni tabulatoru a odradkovani
        $line = preg_replace('~\s{2,}~', " ", $line); // odstraneni po sobe jdoucich mezer

        $line_words = explode(" ", $line);

        // skip empty line or comment
        if (count($line_words) == 0)
        {
            continue;
        }
        else if (preg_match('~#.*~', $line_words[0], $out))
        {
            $stats["com"]++;
            continue;
        }

        // header check
        if ($expecting_header)
        {
            if (preg_match('~^(\s)*((.IPPcode20(\s)+#+)|(.IPPcode20)(\s)*$)~', $line, $out))
            {
                $expecting_header = false;
                continue;
            }
            else
            {
                fwrite(STDERR, "Missing header\n");
                exit(ExitCodesEnum::InvalidHeader);
            }
        }

        $line_words[0] = strtolower($line_words[0]);
        
        if (array_key_exists($line_words[0], $iia)) // prikaz je platny
        {
            


            if (count($line_words) > count($iia[$line_words[0]])) // prikaz ma dostatecny pocet parametru
            {
                $word_index = 1;
                foreach ($iia[$line_words[0]] as $expected_param_index) // kontrola ze argumenty jsou pozadovaneho typu
                {
                    if (!preg_match($param_regex[$expected_param_index], $line_words[$word_index], $out))
                    {
                        // echo $expected_param_pattern;
                        echo "neplatny parametr\n";
                        exit(1);
                    }
                    $word_index++;
                }

                if (array_key_exists($word_index, $line_words)) // kontrola ze za prikazem je bud komentar, nebo nic
                {
                    if (!preg_match('~#.*~', $line_words[$word_index], $out))
                    {
                        echo "neznamy lexem za prikazem \n";
                        exit(1);
                    }
                    else
                    {
                        $stats["com"]++;
                    }
                }

                // nastaveni tagu instruction
                $xml_instruction = $xml_dom->createElement('instruction');
                $xml_instruction->setAttribute('order', strval($counter));
                $xml_instruction->setAttribute('opcode', strval(strtoupper($line_words[0])));


                // pripnuti argumentu do xml
                for ($i = 1; $i < 4; $i++)
                {
                    if (array_key_exists($i, $line_words))
                    {
                        $xml_arg = $xml_dom->createElement('arg' . $i);

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
                            echo "neplatny parametr\n";
                            exit(1);
                        }
                        
                        $xml_instruction->appendChild($xml_arg);
                    }
                    else
                    {
                        break;
                    }
                }
                
                $xml_progam->appendChild($xml_instruction);
                $stats["loc"]++;
            }
            else
            {
                // echo count($line_words);
                // echo count($param_regex);
                echo "nedostatecny pocet parametru\n";
                exit(1);
            }

            // label statistics
            if ("label" == $line_words[0])
            {
                if (!in_array($line_words[1], $labels))
                {
                    array_push( $labels, $line_words[1]);
                    $stats["lab"]++;
                }
            }

            if ("jump" == $line_words[0] || "jumpifeq" == $line_words[0] || "jumpifneq" == $line_words[0])
            {
                $stats["jum"]++;
            }
        }
        else if (preg_match('~#.*~', $line_words[0], $out)) // komentar
        {
            echo "WTF TADY KOMENTAR?\n"; // todo delete
        }
        else if (empty($line_words[0])) // prazdny radek
        {
            // echo "prazdny radek\n";
            continue;
        }
        else
        {
            // var_dump($line_words);
            echo "neznamy prikaz\n";
            echo $line;
            exit(1);
        }

        $counter++;
    }

    // Header('Content-type: text/xml');
    // print($xml->asXML()); delete
    echo $xml_dom->saveXML();

    // TODO UTF-8 kodovani
    // TODO check regexes

?>