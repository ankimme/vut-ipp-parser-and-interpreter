#!/usr/bin/env php7.4

<?php

    // function run_parser_test($parse_script, $src_file, $out_file, $rc_file)
    // {
    //     $shell_out = shell_exec('php7.4 ' . $parse_script . ' < ' . $src_file);

    //     $test_passed = true;

    //     // java -jar /pub/courses/ipp/jexamxml/jexamxml.jar test.out test.your_out diffs.xml  /D /pub/courses/ipp/jexamxml/options NAVRATOVA_HODNOTA="$?"


    //     return $test_passed;
    // }


    // function change_file_extension($filename, $new_extension)
    // {
    //     $info = pathinfo($filename);
    //     return $info['dirname'] . '/' . $info['filename'] . '.' . $new_extension;

    // }

    interface Tester
    {
        public function run_test_file($file_path);
    }

    class ParseOnlyTester implements Tester
    {
        // $file_path - path of test file, must not contain extension of file
        public function run_test_file($file_path)
        {
            return "Par" . $file_path;
        }
    }

    class IntOnlyTester implements Tester
    {
        // $file_path - path of test file, must not contain extension of file
        public function run_test_file($file_path)
        {
            return "Int" . $file_path;
        }
    }

    class BothTester implements Tester
    {
        // $file_path - path of test file, must not contain extension of file
        public function run_test_file($file_path)
        {
            return "Both" . $file_path;
        }
    }

    class TestResult
    {
        public $rc_parse_real;
        public $rc_parse_expected;
        public $rc_int_real;
        public $rc_int_expected;
        public $result; // bool
    }


    require_once 'exitCodes.php';

    $options = getopt("h", ["help", "directory:", "recursive", "parse-script::", "int-script::", "parse-only", "int-only", "jexamxml::"]);
    
    // process --help argument and stop execution
    if (array_key_exists("help", $options) || array_key_exists("h", $options))
    {
        if (count($options) == 1)
        {
            echo "This script is used to test the functionality of interpret.py and parse.php scripts.\n\n";
            echo "Usage: test.php [-h] [--directory DIRECTORY] [--recursive] [--parse-script FILE] [--int-script FILE] [--parse-only] [--int-only] [--jexamxml FILE] \n\n";
            echo str_pad("    -h, --help:", 30, " ", STR_PAD_RIGHT) . "show help message\n";
            echo str_pad("    --directory DIRECTORY:", 30, " ", STR_PAD_RIGHT) . "path to directory with test files\n";
            echo str_pad("    --recursive:", 30, " ", STR_PAD_RIGHT) . "enables recursive search of test files in subdirectories\n";
            echo str_pad("    --parse-script FILE:", 30, " ", STR_PAD_RIGHT) . "path of parse.php script\n";
            echo str_pad("    --int-script FILE:", 30, " ", STR_PAD_RIGHT) . "path of interpret.py script\n";
            echo str_pad("    --parse-only:", 30, " ", STR_PAD_RIGHT) . "test only parse.php functionality\n";
            echo str_pad("    --int-only:", 30, " ", STR_PAD_RIGHT) . "test only interpret.py functionality\n";
            echo str_pad("    --jexamxml FILE:", 30, " ", STR_PAD_RIGHT) . "path to jexamxml jar file\n";
            exit(ExitCodesEnum::Success);
        }
        else
        {
            fwrite(STDERR, "Help argument cannot be combined with other arguments\n");
            exit(ExitCodesEnum::ArgumentError);
        }
    }

    // process --directory argument and stop execution if path not valid
    if (array_key_exists("directory", $options))
    {
        if (is_dir($options['directory']))
        {
            $test_directory = $options['directory'];
        }
        else
        {
            fwrite(STDERR, "Test directory not found\n");
            exit(ExitCodesEnum::InputFileError);
        }
    }
    else // default value = current directory
    {
        $test_directory = "./";
    }

    // process --recursive argument
    $recursive = array_key_exists("recursive", $options);
    
    // process --parse-only and --int-only and check wrong argument combination
    $parse_only = array_key_exists("parse-only", $options);
    $int_only = array_key_exists("int-only", $options);
    if ($parse_only)
    {
        if ($int_only || array_key_exists("int-script", $options))
        {
            fwrite(STDERR, "Wrong argument combination\n");
            exit(ExitCodesEnum::ArgumentError);
        }
    }
    if ($int_only)
    {
        if ($parse_only || array_key_exists("parse-script", $options))
        {
            fwrite(STDERR, "Wrong argument combination\n");
            exit(ExitCodesEnum::ArgumentError);
        }
    }

    // process --parse-script argument and stop execution if file does not exist
    if (!$int_only)
    {
        $parse_script = array_key_exists("parse-script", $options) ? $options['parse-script'] : 'parse.php';
        if (!is_file($parse_script))
        {
            fwrite(STDERR, "Parse script not found\n");
            exit(ExitCodesEnum::InputFileError);   
        }
    }
    else
    {
        $parse_script = false;
    }

    // process --int-script argument
    if (!$parse_only)
    {
        $interpret_script = array_key_exists("int-script", $options) ? $options['int-script'] : 'interpret.py';
        if (!is_file($interpret_script))
        {
            fwrite(STDERR, "Interpret script not found\n");
            exit(ExitCodesEnum::InputFileError);   
        }
    }
    else
    {
        $interpret_script = false;
    }

    // process --jexamxml
    $jexamxml = array_key_exists("jexamxml", $options) ? $options['jexamxml'] : '/pub/courses/ipp/jexamxml/jexamxml.jar';

    echo "test dir:" . $test_directory . "\n";
    print sprintf("recursive: %b", $recursive) . "\n";
    echo "parser:" . $parse_script . "\n";
    echo "interpret:" . $interpret_script . "\n";
    echo "jexamxml:" . $jexamxml . "\n\n";
    // todo delete

    $test_files_list = array();
    // create list of test files (without extenstion)
    function create_file_list($test_directory, &$output_array, $recursive)
    {
        if ($recursive)
        {
            foreach (glob($test_directory . "/*", GLOB_ONLYDIR) as $directory)
            {
                create_file_list($directory, $output_array, $recursive);
            }
        }
        foreach (glob($test_directory . '/*.src') as $src_file)
        {
            $path_parts = pathinfo($src_file);
            array_push($output_array, $path_parts['dirname'] . '/' . $path_parts['filename']);
        }
    }

    create_file_list($test_directory, $test_files_list, $recursive);

    // generate IN, OUT, RC if not existing already
    foreach ($test_files_list as $file)
    {
        $in_file = $file . '.in';
        $out_file = $file . '.out';
        $rc_file = $file . '.rc';
        
        if (!is_file($in_file))
        {
            $f = fopen($in_file, "w");
            if (!$f)
            {
                fwrite(STDERR, "Could not create file\n");
                exit(ExitCodesEnum::OutputFileError);
            }
            fclose($f);
        }

        if (!is_file($out_file))
        {
            $f = fopen($out_file, "w");
            if (!$f)
            {
                fwrite(STDERR, "Could not create file\n");
                exit(ExitCodesEnum::OutputFileError);
            }
            fclose($f);
        }

        if (!is_file($rc_file))
        {
            $f = fopen($rc_file, "w");
            if (!$f)
            {
                fwrite(STDERR, "Could not create file\n");
                exit(ExitCodesEnum::OutputFileError);
            }
            fwrite($f, "0");
            fclose($f);
        }
    }

    if ($parse_only)
    {
        $tester = new ParseOnlyTester();
    }
    elseif ($int_only)
    {
        $tester = new IntOnlyTester();
    }
    else
    {
        $tester = new BothTester();
    }


    foreach ($test_files_list as $file)
    {
        $test_result = $tester->run_test_file($file);
        echo $test_result . "\n"; delt
    }
?>
