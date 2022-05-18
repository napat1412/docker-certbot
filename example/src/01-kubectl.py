mport os
#os.system("chmod +x /usr/src/python/dns-update.sh")

KUBECTL_VER="v1.11.6"

KUBECTL_PATH="/mnt/bin/kubectl"

if not os.path.isfile(KUBECTL_PATH):
  print("Install kubectl")
  os.system("mkdir -p {0}".format(KUBECTL_PATH))
  os.system("rm -rf {0}".format(KUBECTL_PATH))
  KUBECTL_PATH_TMP=KUBECTL_PATH+".tmp"
  os.system("wget -O "+KUBECTL_PATH_TMP+" http://storage.googleapis.com/kubernetes-release/release/"+KUBECTL_VER+"/bin/linux/amd64/kubectl")
  os.system("mv "+KUBECTL_PATH_TMP+" "+KUBECTL_PATH)
  os.system("chmod a+x "+KUBECTL_PATH)
print("kubectl is installed")
