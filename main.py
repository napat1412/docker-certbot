import os

def child(pythonFile):
   print("A new child: {0} run python file: {1}".format( os.getpid(), pythonFile))
   os.system("python -u {0}".format(pythonFile))
   os._exit(0)

PYTHON_APP = "/usr/src/python"
childPID_list = []

##### install PIP_MODULE #####
pip_module = os.getenv('PIP_MODULE', "")
print("Installing PIP_MODULE: {0}".format(pip_module))
os.system("pip install --no-cache-dir {0}".format(pip_module))

##### list PYTHON_APP and fork it #####
files = os.listdir(PYTHON_APP)
for file in files:
  isPythonFile = file.endswith(".py")
  if isPythonFile:
    print("PYTHON APP:{0} FILE:{1}".format(isPythonFile, file))
    pythonFile = "{0}/{1}".format(PYTHON_APP,file)

    newpid = os.fork()
    if newpid == 0:
       child(pythonFile)
    else:
      pids = (os.getpid(), newpid)
      print("parent: %d, child: %d\n" % pids)
      childPID_list.append(newpid)

for childPID in childPID_list:
  os.waitpid(childPID,0)
  print("child pid: {0} is terminated".format(childPID))

print("Exit main.py")
