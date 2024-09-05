# Parser and Interpreter of IPPcode20

### Course
[Principles of Programming Languages](https://www.fit.vut.cz/study/course/IPP/.en) 2019/20

### Aim
The project was divided into three parts:

1. **Parser:** Parse the fiction language IPPcode20 into XML format. IPPcode20 is described in Section 6 of `task.pdf`.
2. **Interpreter:** Interpret the IPPcode20 code converted to XML.
3. **Tests:** Run the parser, interpreter, or both in a pipeline.

### How to Run  
**parse.php**  

```
php7.4 parse.php < input.IPPcode20 > output.xml
```

**interpret.py**  

```
python3.8 interpret.py --input="file" --source="file"
```

**test.php**  

```
php7.4 test.php --recursive --int-only (or --parse-only) --parse-script="file" --int-script="file" --directory="path" --jexamxml="file"
```

### Other Files
- **task.pdf:** Assignment (CZ).
- **readme1.pdf:** Documentation of parser.
- **readme2:** Documentation of interpreter.
