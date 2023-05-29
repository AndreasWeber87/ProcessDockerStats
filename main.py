import os.path
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


# Remove idle lines (with CPU<0,5%) at the beginning of each test (for example AddTest) in the list
def __removeIdleLinesAtBeginning(lines: list):
    newLines = []
    testType = ""
    isLineAtBeginningOfTest = False

    for i in range(len(lines)):
        columns = lines[i].split(";")

        if testType != columns[1]:  # begin of a new test
            isLineAtBeginningOfTest = True
            testType = columns[1]

        if float(columns[4]) > 0.5:  # CPU != 0%
            if isLineAtBeginningOfTest and i > 1:  # add last line with CPU<0.5%
                newLines.append(lines[i - 1])

            isLineAtBeginningOfTest = False
            newLines.append(lines[i])
            continue
        elif not isLineAtBeginningOfTest:
            newLines.append(lines[i])

    return newLines


def __writeAllStatsToFile(filename: str, columns: str, lines: list):
    with open(os.path.join(r"C:\Users\Andi\Desktop\Bac\_Builds", filename), "w") as file:
        file.write(columns + "\n")

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


def __writeTestStatsToFile(filename: str, lines: list, nameOfTest: str, nameOfContainer: str, columnToWrite: int):
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

    for i in range(maxLenOfBlock):
        newLine = f"{nameOfContainer};{nameOfTest}"

        for block in blockList:
            if len(block) <= i:
                newLine += ";;;"
                continue

            columns = block[i].split(";")
            newLine += f";{columns[0]};{columns[2]};{columns[columnToWrite]}"

        newLines.append(newLine)

    with open(os.path.join(r"C:\Users\Andi\Desktop\Bac\_Builds", filename), "w") as file:
        for line in newLines:
            file.write(line.replace(".", ",") + "\n")


if __name__ == "__main__":
    try:
        filenameSrc = r"C:\Users\Andi\Desktop\Bac\_Builds\docker_raw_stats.csv"
        columns = """Time;\
Test Name;\
Test Number;\
Container;\
CPU [%];\
MEM Usage [MiB];\
MEM Limit [MiB];\
NET Input [MB];\
NET Output [MB];\
Block Input [MB];\
Block Output [MB]"""

        with open(filenameSrc, "r") as file:
            lines = file.readlines()

        lines = __removeUnnecessaryLines(lines)
        lines = __formatLines(lines)
        lines = __removeIdleLinesAtBeginning(lines)
        lines.reverse()
        lines = __removeIdleLinesAtBeginning(lines)
        lines.reverse()

        __writeAllStatsToFile("docker_stats.csv", columns, lines)

        for container in ["running-go-api", "running-nodejs-api", "running-python-api"]:
            for testname in ["AddTest", "ChangeTest", "GetTest", "DeleteTest"]:
                __writeTestStatsToFile(f"docker_stats_{testname}_{container}.csv", lines, testname, container, 4)

    except Exception:
        traceback.print_exc()
