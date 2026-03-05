using Pkg
Pkg.rm("PyCall")
Pkg.add("PyCall")
ENV["PYTHON"] = raw"C:\Users\yoshi\py_benchmark_test\.venv\Scripts\python.exe"
Pkg.build("PyCall")
using PyCall
println("PyCall reinstalled and configured for: ", PyCall.python)