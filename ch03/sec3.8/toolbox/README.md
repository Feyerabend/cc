
## Building your own Toolbox

Just as a carpenter understands the intricacies of their craft well enough
to identify gaps in their toolkit and create custom solutions, a developer
can do the same in the world of software. Whether it's writing a specialized
debugging tool, creating a tailor-made profiler, or developing a unique
scripting language to optimize a specific workflow, developers have
the ability to shape their tools to meet their precise needs.

This ability to craft tools not only enhances efficiency but also fosters
a deeper understanding of the systems being worked on. Just as a custom
woodworking jig can ensure precision in a fine cabinet, a well-designed
software tool can streamline development and debugging, often solving
problems that off-the-shelf tools cannot fully address. Embracing this
mindset turns tool creation into a natural extension of problem-solving,
reflecting both creativity and technical expertise.

I can testify to this as I have a background in education as a cabinetmaker.
As a cabinetmaker, you sometimes have the opportunity to craft your own tools.
The same principle can many times apply to developers.

To make things more transparent, we turn our attention to tools for our previous
virtual machines. This serves a dual purpose: not only can you enhance these
tools to deepen your understanding, but the process of improvement itself helps
to clarify the underlying ideas and principles behind them.
Additionally, working with the corresponding professional tools will expand
your skillset and equip you with the expertise needed to advance in your work.


### Debugging

Debugging has been an integral part of computing since
the early days of programming. Early debugging tools were
fundamental yet highly effective. Techniques such as logging,
single-stepping through code, and setting breakpoints to halt
execution for detailed inspection were very useful. These
methods allowed developers to meticulously trace and resolve
issues. In this exploration, we'll revisit these simple but
powerful debugging tools and see how they are still relevant
when working with virtual machines.

- [Debugging](./debug)


### Assembling & Disassembling

Taking an assembler from a previous chapter, we can turn it into something which
analyses our "machine code," a disassembler. It reverses the process,
takes the integers and turn them into easier to understandable mnemonics,
the "assembly language."

The assembler works as previously:

```shell
   > python3 asm.py -i sample.a -o sample.b
   > python3 asm.py -i callret.a -o callret.b
   > python3 asm.py -i fact.a -o callret.b
   > ls
   ..
   callret.a   fact.a      sample.a
   callret.b   fact.b      sample.b
   ..
```

#### Disassembler

If we take the following 'binary' in 'sample.b':

```code
38,13,0,28,0,12,0,27,1,5,11,16,27,1,30,
0,24,12,0,27,1,31,28,3,12,3,29,0,2,0,12,
0,14,0,18,30,0,24,24,27,10,29,0,2,0,14,
0,22,8
```

we can convert it into what it previously was
assembled from:

```shell
    > python3 disasm.py -i sample.b -o sample.d
    > cat sample.d
```

```assembler
L0:
	LDARG 0     # 013 000
	ST 0        # 028 000
	LD 0        # 012 000
	SET 1       # 027 001
	EQ          # 005
	JPZ :L16    # 011 016
	SET 1       # 027 001
	STORE 0     # 030 000
	RET         # 024
L16:
	LD 0        # 012 000
	SET 1       # 027 001
	SUB         # 031
	ST 3        # 028 003
	LD 3        # 012 003
	STARG 0     # 029 000
	CALL :L0    # 002 000
	LD 0        # 012 000
	LOAD 0      # 014 000
	MUL         # 018
	STORE 0     # 030 000
	RET         # 024
	RET         # 024
START:
	SET 10      # 027 010
	STARG 0     # 029 000
	CALL :L0    # 002 000
	LOAD 0      # 014 000
	PRINT       # 022
	HALT        # 008
```

Disassemblers can be useful, when e.g. the source isn't available
or when you want to inspect the machine and the program in this
context.

- [Assember/Disassembler](./asm)


### Static Analyser

Static analysis examines code *without executing* it. It checks for potential issues
like syntax errors, incorrect instruction formats, or misuse of variables. In the
provided example, the static analyzer validates the REGVM program by ensuring valid
opcodes, correct argument counts, proper register usage, and jump target resolution
before even running the code.

- [Static Analyser](./static)


### Profiling

Profiling tools are software utilities designed to analyze a program's performance
characteristics during execution. They provide insights into aspects like execution
time, memory usage, function call frequency, and resource utilization. By collecting
and visualising this data, profiling tools help identify bottlenecks, inefficiencies,
or excessive resource consumption, enabling developers to optimize their code for
speed, efficiency, or scalability.

- [Profiler](./prof)


### Diagnostics with Statistics

To gain deeper insights into how programs execute on our virtual machine and to
identify opportunities for improvement, statistical analysis can be an invaluable
tool. In this case, we have opted to use Bayesian techniques to perform a
post-mortem analysis, examining the program's behavior after its execution.

By leveraging Bayesian methods, we can infer probabilities and relationships from
the execution logs generated during the program's runtime. These techniques allow
us to model uncertainties and dependencies in a principled way, enabling more
informed decisions about optimization and debugging. For example, Bayesian analysis
could help identify which execution paths are most likely to lead to errors or
performance bottlenecks, or it could quantify the likelihood of certain variables
taking specific values under varying conditions.

This approach goes beyond simple descriptive statistics by incorporating prior
knowledge or assumptions into the analysis. As a result, it offers a more nuanced
understanding of program behavior, even in cases where the data may be sparse or
noisy. By iterating on these insights, we can refine both the virtual machine's
design and the programs that run on it.

- [Diagnostics](./diag)

