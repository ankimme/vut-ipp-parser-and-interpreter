#!/usr/bin/env php7.4

<?php

    function run_parser_test($parse_script, $src_file, $out_file, $rc_file)
    {
        $shell_out = shell_exec('php7.4 ' . $parse_script . ' < ' . $src_file);

        $test_passed = true;

        // java -jar /pub/courses/ipp/jexamxml/jexamxml.jar test.out test.your_out diffs.xml  /D /pub/courses/ipp/jexamxml/options NAVRATOVA_HODNOTA="$?"


        return $test_passed;
    }


    function change_file_extension($filename, $new_extension)
    {
        $info = pathinfo($filename);
        return $info['dirname'] . '/' . $info['filename'] . '.' . $new_extension;

    }

    require_once 'exitCodes.php';

    $options = getopt("h", ["help", "directory:", "recursive", "parse-script::", "int-script::", "parse-only", "int-only", "jexamxml::"]);

    
    // process --help argument
    if (array_key_exists("help", $options) || array_key_exists("h", $options))
    {
        if (count($options) == 1)
        {
            echo "This script is used to test the functionality of interpret.py and parse.php scripts.\n\n";
            echo "Usage: test.php [-h] [--direcotry DIRECTORY] [--recursive] [--parse-script FILE] [--int-script FILE] [--parse-only] [--int-only] [--jexamxml FILE] \n\n";
            echo str_pad("    -h, --help:", 30, " ", STR_PAD_RIGHT) . "show help message\n";
            echo str_pad("    --direcotry DIRECTORY:", 30, " ", STR_PAD_RIGHT) . "path to directory with test files\n";
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


    // process --directory argument
    if (array_key_exists("directory", $options))
    {
        if (file_exists($options['directory'])) // todo and is really a directory
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
    
    // process --recursive argument
    // if (array_key_exists("parse-script", $options))
    // {
    //     if (file_exists($options['parse-script']))
    //     {
    //         $parse_script = $options['parse-script'];
    //     }
    //     else
    //     {
    //         fwrite(STDERR, "Parse script not found\n");
    //         exit(ExitCodesEnum::InputFileError);   
    //     }
    // }

    // process --parse-script argument
    $parse_script = array_key_exists("parse-script", $options) ? $options['parse-script'] : 'parse.php';
    // if (!file_exists($parse_script))
    // {
    //     fwrite(STDERR, "Parse script not found\n");
    //     exit(ExitCodesEnum::InputFileError);   
    // }

    // process --int-script argument
    $interpret_script = array_key_exists("int-script", $options) ? $options['int-script'] : 'interpret.py';
    // if (!file_exists($interpret_script))
    // {
    //     fwrite(STDERR, "Interpret script not found\n");
    //     exit(ExitCodesEnum::InputFileError);   
    // }

    // var_dump($options);
    //test directory
    // if ($handle = opendir($test_directory)) {

    //     while (false !== ($entry = readdir($handle))) {
    
    //         if ($entry != "." && $entry != "..") {
    
    //             echo "$entry\n";
    //         }
    //     }
    
    //     closedir($handle);
    // }

    // process --parse-only and --int-only
    $parse_only = array_key_exists("parse-only", $options);
    $int_only = array_key_exists("parse-only", $options);
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

    // process --jexamxml
    $jexamxml = array_key_exists("jexamxml", $options) ? $options['jexamxml'] : '/pub/courses/ipp/jexamxml/jexamxml.jar';

    echo "test dir:" . $test_directory . "\n";
    echo "parser:" . $parse_script . "\n";
    echo "interpret:" . $interpret_script . "\n";
    echo "jexamxml:" . $jexamxml . "\n\n";
    // todo delete
    
    

    /* recursive dir todo
    $directory = new RecursiveDirectoryIterator($test_directory);
    $iterator = new RecursiveIteratorIterator($directory);
    $regex = new RegexIterator($iterator, '~^.+\.src$~i', RecursiveRegexIterator::GET_MATCH);

    var_dump($regex);
    var_dump($iterator);


    foreach ($regex as $file)
    {
        echo $file->
        var_dump($file);
    }
    // function getSrcFiles
    */

    // $src_file = array();
    foreach (glob($test_directory . '/*.src') as $src_file)
    {
        // echo $src_file . "\n"; // todo delete

        $out_file = change_file_extension($src_file, 'out');
        $rc_file = change_file_extension($src_file, 'rc');

        // echo $src_file . "\n";
        // echo $out_file . "\n";
        // echo $rc_file . "\n";

        $test_passed = run_parser_test($parse_script, $src_file, $out_file, $rc_file);
        echo basename($src_file) . ": " . $test_passed . "\n";
    }
    
    echo "done\n"; // todo delete
?>
