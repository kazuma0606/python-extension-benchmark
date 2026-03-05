using Pkg
ENV["PYTHON"] = raw"C:\Users\yoshi\py_benchmark_test\.venv\Scripts\python.exe"
Pkg.build("PyCall")
using PyCall
println("PyCall configured for: ", PyCall.python)