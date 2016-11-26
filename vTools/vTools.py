#!/usr/bin/env python3
import sys
import re
import pprint as pp

# TODO
# grab module name ---------------------------------- DONE
# search for port only between module and ); -------- DONE
# add parameter recognition
# error handler for sys.argv
# error handler for invalid paths


# define regex for verilog module header
modulePattern = (r"^\s*module\s+"               # module keyword
                 r"([\w_\$]+)")                 # module name
regexModule = re.compile(modulePattern)

# define regex for verilog module close
closeModulePattern = r"\);$"                     # close of module declaration
regexCloseModule = re.compile(closeModulePattern)

# define regex for verilog port definition
portPattern = (r"^\s*(input|output|inout)\s+"    # port direction
               r"((wire|reg)\s+)"                # data type
               r"(\[\s*\d+\d*:\s*\d+\s*\]\s+)?"  # port size
               r"([\w_\$]+){1}")                 # port name
regexPort = re.compile(portPattern)


# get path to file to be analyzed
FILE = sys.argv[1]


# extract module name and port definitions
with open(FILE, 'r') as sourceFile:
    moduleFlag = False
    moduleCloseFlag = False
    portList = []

    for line in sourceFile:

        if moduleFlag is False:
            moduleMatch = regexModule.match(line)
            if moduleMatch:
                portList.append(moduleMatch.group(1))
                moduleFlag = True

        moduleCloseFlag = True if regexCloseModule.match(line) else moduleCloseFlag

        if moduleFlag is True:
            portMatch = regexPort.match(line)
            if portMatch is not None:
                portList.append(portMatch.group().split())
                # print(match.group().split())

        if moduleCloseFlag is True:
            break
    # pp.pprint(portList)


# create testbench template
testbenchFileName = portList[0] + '_tb.v'

with open(testbenchFileName, 'w') as testFile:
    testFile.write("`timescale 1ns / 1ps")
    testFile.write("\n\nmodule {}_tb();".format(portList[0]))

    """ generate force signals
    Two different port formats:
        length 3: [0] direction, [1] data type, [2] port name
        length 4: [0] direction, [1] data type, [2] port size, [3] port name
    """
    iterPorts = iter(portList)
    next(iterPorts)
    testFile.write("\n\n/* --- signal declaration for UUT --- */")
    for port in iterPorts:
        if len(port) == 3:
            if port[0] == "input" or port[0] == "inout":
                testFile.write("\n\treg {};".format(port[2]))
            elif port[0] == "output":
                testFile.write("\n\twire {};".format(port[2]))
        elif len(port) == 4:
            if port[0] == "input" or port[0] == "inout":
                testFile.write("\n\treg {} {};".format(port[2], port[3]))
            elif port[0] == "output":
                testFile.write("\n\twire {} {};".format(port[2], port[3]))

    """ generate UUT
    """
    iterPorts = iter(portList)
    testFile.write("\n\n/* --- UUT --- */")
    testFile.write("\n{} UUT\t(".format(next(iterPorts)))

    totalPorts = len(portList) - 2
    currentPort = 0

    for port in iterPorts:
        if len(port) == 3:
            if currentPort != totalPorts:
                testFile.write("\n\t.{}({}),".format(port[2], port[2]))
            else:
                testFile.write("\n\t.{}({}),".format(port[2], port[2]))
            currentPort += 1
        elif len(port) == 4:
            if currentPort != totalPorts:
                testFile.write("\n\t.{}({}),".format(port[3], port[3]))
            else:
                testFile.write("\n\t.{}({})".format(port[3], port[3]))
            currentPort += 1
            # print("DEBUG: Total: {}, Current: {}".format(totalPorts, currentPort))
    testFile.write("\n);")

    """ clock generator
    """
    testFile.write("\n\n/* --- clock signal generator --- */")
    testFile.write("\nalways begin")
    testFile.write("\n\tclk = 1'b0")
    testFile.write("\n\t#(10)")
    testFile.write("\n\tclk = 1'b1")
    testFile.write("\n\t#(10)")
    testFile.write("\nend")

    """ generate initial block
    """
    testFile.write("\n\n/* --- initial block --- */")
    testFile.write("\ninitial begin")
    testFile.write("\n\t$finish;")
    testFile.write("\nend")

    """ endmodule
    """
    testFile.write("\n\nendmodule")
