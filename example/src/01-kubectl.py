import os

KUBECTL_PATH="/usr/local/bin"
MASTER_HOST="172.16.0.220"
SSL_PATH="/mnt/kube-ssl"
CA_CERT="{0}/ca.pem".format(SSL_PATH)
ADMIN_KEY="{0}/admin-key.pem".format(SSL_PATH)
ADMIN_CERT="{0}/admin.pem".format(SSL_PATH)

print("Install kubectl")
os.system("wget -O "+KUBECTL_PATH+"/kubectl http://storage.googleapis.com/kubernetes-release/release/v1.5.4/bin/linux/amd64/kubectl")
os.system("chmod a+x "+KUBECTL_PATH+"/kubectl")

os.system("kubectl config set-cluster default-cluster --server=https://"+MASTER_HOST+" --certificate-authority="+CA_CERT)
os.system("kubectl config set-credentials default-admin --certificate-authority="+CA_CERT+" --client-key="+ADMIN_KEY+" --client-certificate="+ADMIN_CERT)
os.system("kubectl config set-context default-system --cluster=default-cluster --user=default-admin")
os.system("kubectl config use-context default-system")
