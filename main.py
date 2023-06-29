import os.path
import sys
import traceback


def __convertToMiB(value: str):
    if "MiB" in value:
        return str(float(value.replace("MiB", "")))
    elif "GiB" in value:
        return str(float(value.replace("GiB", "")) * 1024)
    else:
        raise Exception(f"unknown value: {value}")


def __convertToMB(value: str):
    if "kB" in value:
        return str(float(value.replace("kB", "")) / 1000)
    elif "MB" in value:
        return str(float(value.replace("MB", "")))
    elif "GB" in value:
        return str(float(value.replace("GB", "")) * 1000)
    elif "B" in value:
        return str(float(value.replace("B", "")) / 1_000_000)
    else:
        raise Exception(f"unknown value: {value}")


def __removeUnnecessaryLines(lines: list):
    newLines = []

    for line in lines:
        if line.startswith("Time"):
            continue
        if len(line.split(";")) != 11:
            continue
        newLines.append(line.replace("\n", ""))

    return newLines


def __formatLines(lines: list):
    newLines = []

    for line in lines:
        columns = line.split(";")

        columns[4] = columns[4].replace("%", "")  # CPU
        columns[5] = __convertToMiB(columns[5])  # MEM Usage
        columns[6] = __convertToMiB(columns[6])  # MEM Limit
        columns[7] = __convertToMB(columns[7])  # NET Input
        columns[8] = __convertToMB(columns[8])  # NET Output
        columns[9] = __convertToMB(columns[9])  # Block Input
        columns[10] = __convertToMB(columns[10])  # Block Output

        newLines.append(";".join(columns))

    return newLines


# Remove idle lines (with CPU < 2%)
def __removeIdleLines(lines: list):
    newLines = []

    for line in lines:
        columns = line.split(";")

        if float(columns[4]) > 2:  # CPU is not in idle (> 2%)
            newLines.append(line)

    return newLines


def __writeAllStatsToFile(filename: str, lines: list):
    columnNames = """Time;\
    Test;\
    Test Name;\
    Container;\
    CPU [%];\
    MEM Usage [MiB];\
    MEM Limit [MiB];\
    NET Input [MB];\
    NET Output [MB];\
    Block Input [MB];\
    Block Output [MB]"""

    with open(filename, "w") as file:
        file.write(columnNames + "\n")

        for line in lines:
            file.write(line.replace(".", ",") + "\n")


def __linesToTestBlocks(lines: list):
    allTests = []
    testBlock = []
    lastTestNumber = ""

    for line in lines:
        testNumber = line.split(";")[2]

        if lastTestNumber != testNumber:
            lastTestNumber = testNumber

            if len(testBlock) > 0:
                allTests.append(testBlock)
                testBlock = []

        testBlock.append(line)

    allTests.append(testBlock)
    return allTests


def __writeTestStatsToFile(filename: str, lines: list, nameOfTest: str, nameOfContainer: str,
                           columnToWrite: int, columnToWriteName: str):
    filteredLines = []

    for line in lines:
        columns = line.split(";")

        if columns[1] == nameOfTest and columns[3] == nameOfContainer:
            filteredLines.append(line)

    if len(filteredLines) == 0:
        return

    blockList = __linesToTestBlocks(filteredLines)
    maxLenOfBlock = max(len(x) for x in blockList)
    newLines = []
    firstLine = "Container;Test;"

    for i in range(len(blockList)):
        firstLine += f"Time ({str(i + 1)});Test Name ({str(i + 1)});{columnToWriteName} ({str(i + 1)});"
    newLines.append(firstLine)

    for i in range(maxLenOfBlock):
        newLine = f"{nameOfContainer};{nameOfTest}"

        for block in blockList:
            if len(block) <= i:
                newLine += ";;;"
                continue

            columns = block[i].split(";")
            newLine += f";{columns[0]};{columns[2]};{columns[columnToWrite]}"

        newLines.append(newLine)

    with open(filename, "w") as file:
        for line in newLines:
            file.write(line.replace(".", ",") + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 1:
        print("The path of the .csv file must be the first parameter!")
        quit()

    filenameSrc = sys.argv[1]

    if not os.path.exists(filenameSrc):
        print("The path of the .csv file must be the first parameter!")
        quit()

    foldername = os.path.dirname(filenameSrc)

    try:
        with open(filenameSrc, "r") as file:
            lines = file.readlines()

        lines = __removeUnnecessaryLines(lines)
        lines = __formatLines(lines)
        lines = __removeIdleLines(lines)

        __writeAllStatsToFile(os.path.join(foldername, "docker_stats.csv"), lines)

        for container in ["running-go-api", "running-nodejs-api", "running-python-api"]:
            for testname in ["AddTest", "ChangeTest", "GetTest", "DeleteTest", "AllTests"]:
                __writeTestStatsToFile(os.path.join(foldername, f"docker_stats_{testname}_{container}_cpu.csv"), lines,
                                       testname, container, 4, "CPU [%]")
                __writeTestStatsToFile(os.path.join(foldername, f"docker_stats_{testname}_{container}_memory.csv"), lines,
                                       testname, container, 5, "MEM Usage [MiB]")

    except Exception:
        traceback.print_exc()
