<?php

    /**
     * Interface of tester classes
     */
    interface TesterInterface
    {
        public function run_test_file($file_path);
    }

    /**
     * Used when testing only parse.php
     */
    class ParseOnlyTester implements TesterInterface
    {
        function __construct($parse_script, $jexamxml) {
            $this->parse_script = $parse_script;
            $this->jexamxml = $jexamxml;
        }

        public $test_mode = "Parser only";

        /**
         * Run a single test of parse.php
         * 
         * @param $file_path Path of the test file WITHOUT extenstion
         * @return TestResult Results of the test as an object
         */
        public function run_test_file($file_path)
        {
            $test_result = new TestResult();
            $test_result->test_file = $file_path;

            $src_file_path = $file_path . ".src";
            $rc_file_path = $file_path . ".rc";
            $out_file_path = $file_path . ".out";
            $real_out_file_path = $file_path . ".real_out";

            $test_result->expected_rc = file_get_contents($rc_file_path);

            exec('php7.4 ' . $this->parse_script . ' < ' . $src_file_path . ' > ' . $real_out_file_path, $dev_null, $test_result->real_rc);
            
            if ($test_result->expected_rc == '0')
            {
                if ($test_result->real_rc == '0')
                {
                    $delta_file_path = $file_path . ".delta";
                    // exec("java -jar $this->jexamxml $real_out_file_path $out_file_path $delta_file_path", $jexamsml_output, $jexamxml_rc); use this if not executing on server Merlin
                    exec("java -jar $this->jexamxml $real_out_file_path $out_file_path $delta_file_path /pub/courses/ipp/jexamxml/options", $jexamsml_output, $jexamxml_rc);
                    unlink($delta_file_path);
                    if ($jexamxml_rc == 0)
                    {
                        $test_result->comparison = 1;
                        $test_result->test_ok = true;
                    }
                    else
                    {
                        $test_result->comparison = -1;
                        $test_result->test_ok = false;
                    }
                }
                else
                {
                    $test_result->comparison = 0;
                    $test_result->test_ok = false;
                } 
            }
            else
            {
                if ($test_result->real_rc == $test_result->expected_rc)
                {
                    $test_result->comparison = 0;
                    $test_result->test_ok = true;
                }
                else
                {
                    $test_result->comparison = 0;
                    $test_result->test_ok = false;
                }
            }

            unlink($real_out_file_path);
            return $test_result;
        }
    }

    /**
     * Used when testing only interpret.py
     */
    class IntOnlyTester implements TesterInterface
    {
        function __construct($int_script, $jexamxml) {
            $this->int_script = $int_script;
            $this->jexamxml = $jexamxml;
        }

        public $test_mode = "Interpret only";

        /**
         * Run a single test of interpret.py
         * 
         * @param $file_path Path of the test file WITHOUT extenstion
         * @return TestResult Results of the test as an object
         */
        public function run_test_file($file_path)
        {
            $test_result = new TestResult();
            $test_result->test_file = $file_path;

            $src_file_path = $file_path . ".src";
            $rc_file_path = $file_path . ".rc";
            $in_file_path = $file_path . ".in";
            $out_file_path = $file_path . ".out";
            $real_out_file_path = $file_path . ".real_out";

            $test_result->expected_rc = file_get_contents($rc_file_path);

            exec('python3.8 ' . $this->int_script . ' --input=' . $in_file_path . ' --source=' . $src_file_path . ' > ' . $real_out_file_path, $dev_null, $test_result->real_rc);


            if ($test_result->expected_rc == '0')
            {
                if ($test_result->real_rc == '0')
                {
                    exec("diff $real_out_file_path $out_file_path", $dev_null, $diff_rc);

                    if ($diff_rc == 0)
                    {
                        $test_result->comparison = 1;
                        $test_result->test_ok = true;
                    }
                    else
                    {
                        $test_result->comparison = -1;
                        $test_result->test_ok = false;
                    }
                }
                else
                {
                    $test_result->comparison = 0;
                    $test_result->test_ok = false;
                } 
            }
            else
            {
                if ($test_result->real_rc == $test_result->expected_rc)
                {
                    $test_result->comparison = 0;
                    $test_result->test_ok = true;
                }
                else
                {
                    $test_result->comparison = 0;
                    $test_result->test_ok = false;
                }
            }

            unlink($real_out_file_path);
            return $test_result;
        }
    }

    /**
     * Used when testing both parse.php and interpret.py
     */
    class BothTester implements TesterInterface
    {
        function __construct($parse_script, $int_script, $jexamxml) {
            $this->parse_script = $parse_script;
            $this->int_script = $int_script;
            $this->jexamxml = $jexamxml;
        }

        public $test_mode = "Both";

        /**
         * Run a single test of parse.php and interpret.py
         * 
         * @param $file_path Path of the test file WITHOUT extenstion
         * @return TestResult Results of the test as an object
         */
        public function run_test_file($file_path)
        {
            $test_result = new TestResult();
            $test_result->test_file = $file_path;

            $src_file_path = $file_path . ".src";
            $rc_file_path = $file_path . ".rc";
            $in_file_path = $file_path . ".in";
            $out_file_path = $file_path . ".out";
            $real_parse_out_file_path = $file_path . ".parse_out";
            $real_int_out_file_path = $file_path . ".int_out";

            $test_result->expected_rc = file_get_contents($rc_file_path);

            exec('php7.4 '. $this->parse_script . ' < ' . $src_file_path . ' > ' . $real_parse_out_file_path, $dev_null, $test_result->real_rc);

            if ($test_result->real_rc == '0')  // parsed successfully
            {
                exec('python3.8 ' . $this->int_script . ' --input=' . $in_file_path . ' --source=' . $real_parse_out_file_path . ' > ' . $real_int_out_file_path, $dev_null, $test_result->real_rc);

                if ($test_result->expected_rc == '0')
                {
                    if ($test_result->real_rc == '0')
                    {
                        exec("diff $real_int_out_file_path $out_file_path", $dev_null, $diff_rc);

                        if ($diff_rc == 0)
                        {
                            $test_result->comparison = 1;
                            $test_result->test_ok = true;
                        }
                        else
                        {
                            $test_result->comparison = -1;
                            $test_result->test_ok = false;
                        }
                    }
                    else
                    {
                        $test_result->comparison = 0;
                        $test_result->test_ok = false;
                    } 
                }
                else
                {
                    if ($test_result->real_rc == $test_result->expected_rc)
                    {
                        $test_result->comparison = 0;
                        $test_result->test_ok = true;
                    }
                    else
                    {
                        $test_result->comparison = 0;
                        $test_result->test_ok = false;
                    }
                }

                unlink($real_int_out_file_path);
            }
            else
            {
                if ($test_result->real_rc == $test_result->expected_rc)
                {
                    $test_result->comparison = 0;
                    $test_result->test_ok = true;
                }
                else
                {
                    $test_result->comparison = 0;
                    $test_result->test_ok = false;
                }
            }

            unlink($real_parse_out_file_path);
            return $test_result;
        }
    }

    /**
     * Used to store values of test results
     */
    class TestResult
    {
        public $test_file;
        public $expected_rc;
        public $real_rc;
        public $comparison; // -1, 0, 1
        public $test_ok; // bool
    }

    /**
     * appliacation exit codes
     */
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
            $test_directory = rtrim($options['directory'], "/");
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
        $int_script = array_key_exists("int-script", $options) ? $options['int-script'] : 'interpret.py';
        if (!is_file($int_script))
        {
            fwrite(STDERR, "Interpret script not found\n");
            exit(ExitCodesEnum::InputFileError);   
        }
    }
    else
    {
        $int_script = false;
    }

    // process --jexamxml
    $jexamxml = array_key_exists("jexamxml", $options) ? $options['jexamxml'] : '/pub/courses/ipp/jexamxml/jexamxml.jar';


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
        $tester = new ParseOnlyTester($parse_script, $jexamxml);
    }
    elseif ($int_only)
    {
        $tester = new IntOnlyTester($int_script, $jexamxml);
    }
    else
    {
        $tester = new BothTester($parse_script, $int_script, $jexamxml);
    }

    $total_tests = 0;
    $successful_tests = 0;
    $wrong_tests = 0;
    $test_result_list = array();
    foreach ($test_files_list as $file)
    {
        $test_result = $tester->run_test_file($file);
        array_push($test_result_list, $test_result);

        $total_tests++;
        if ($test_result->test_ok)
        {
            $successful_tests++;
        }
        else
        {
            $wrong_tests++;
        }
    }

    $percentage = $successful_tests / $total_tests * 100;
    

    include("template.html");

?>
