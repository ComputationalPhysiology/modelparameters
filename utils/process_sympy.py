import os
import shutil
from pathlib import Path


def delete_test_bench_folders():
    for root, dirs, files in os.walk("sympy"):
        for d in dirs:
            if d not in ["tests", "benchmarks"]:
                continue

            p = Path(root).joinpath(d)
            shutil.rmtree(p)
            print("Delete ", p)


def absolute_to_relative_imports():
    for root, dirs, files in os.walk("sympy"):
        for f in files:
            path = Path(root).joinpath(f)
            if path.suffix != ".py":
                continue

            print(path)
            with open(path, "r") as fid:
                code = fid.read()

            parts = path.parent.parts
            # Same level
            code = code.replace("from {}".format(".".join(parts) + "."), "from .")
            if len(parts) > 1:
                code = code.replace(
                    "from {}".format(".".join(parts[:-1]) + "."), "from .."
                )
            if len(parts) > 2:
                code = code.replace(
                    "from {}".format(".".join(parts[:-2]) + "."), "from ..."
                )
            code = code.replace(
                "from sympy import ", "from " + len(parts) * "." + " import "
            )
            code = code.replace(
                "import sympy.", "from " + (len(parts) + 1) * "." + " import sympy."
            )

            with open(path, "w") as fid:
                fid.write(code)


if __name__ == "__main__":
    delete_test_bench_folders()
    absolute_to_relative_imports()
