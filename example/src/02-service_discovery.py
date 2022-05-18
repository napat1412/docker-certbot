import sched, time
import subprocess, re, os
import redis

KUBECTL_PATH="/mnt/bin/kubectl"
SERVICE_INDEX_DICT={}

s = sched.scheduler(time.time, time.sleep)
SignedCustomDomain_list = []
SignedClusterDomain_list = []
DomainSuffix = ".web.meca.in.th"
EMAIL = "napat.chu@gmail.com"

RedisHost = "redis.default.svc.cluster.local"
RedisPort = 6379
RedisDB = 1
RedisPasswd = "password"

TTL = 120

### redis_set() update Custom Domain to Redis Server
def redis_set(CustomDomain_list):
  global RedisHost
  global RedisPort
  global RedisDB
  global RedisPasswd
  global TTL
  if len(CustomDomain_list) > 0:
    r = redis.StrictRedis(host=RedisHost, port=RedisPort, db=RedisDB, password=RedisPasswd)
    for domain in CustomDomain_list:
      r.set(domain[0],domain[1],TTL+86400)

### reset_domain() set schedule to run itself periodly
def reset_domain(OffsetTime=86400):
  global s
  global SignedCustomDomain_list
  global SignedClusterDomain_list

  print("EVENT: Reset Domain")

  ### clear list of signed certificates for renew certificates again 
  SignedClusterDomain_list = []
  SignedCustomDomain_list = []

  now = time.time()
  s.enterabs(now+OffsetTime, 0, reset_domain, (OffsetTime,))

### renew_custom_domain() set schedule to run itself periodly
def renew_custom_domain(OffsetTime=600):
  global s

  #print("EVENT: Renew custom domain")
  #os.system("date")
  request_custom_certificate()              # request custom certificate
  now = time.time()
  s.enterabs(now+OffsetTime, 0, renew_custom_domain, (OffsetTime,))

### renew_cluster_domain() set schedule to run itself periodly
def renew_cluster_domain(OffsetTime=600):
  global s

  #print("EVENT: Renew cluster domain")
  #os.system("date")
  request_cluster_certificate()             # request wildcard certificate per namespace
  now = time.time()
  s.enterabs(now+OffsetTime, 0, renew_cluster_domain, (OffsetTime,))

'''
### request_cluster_certificate() request wildcard certificate for each namespace
### (*.<namespace>.web.box-box.space) by using certbot dns challenge
'''
def request_cluster_certificate():
  global s
  global SignedClusterDomain_list
  global DomainSuffix
  global KUBECTL_PATH
  global SERVICE_INDEX_DICT
  global EMAIL
  WildcardClusterDomain_list = []
  
  CertbotDNSchallenge = "certbot certonly --preferred-challenges=dns \
    --config-dir /mnt/letsencrypt/ \
    --server https://acme-v02.api.letsencrypt.org/directory \
    --dns-google \
    --dns-google-credentials /usr/src/python/dns-google.json \
    --dns-google-propagation-seconds 75 \
    --agree-tos --non-interactive --manual-public-ip-logging-ok \
    -m {0} -d".format(EMAIL)
  
  #Get Namespace to create wildcard cluster domain (*.<namespace>.web.box-box.space)
  stdout, stderr = subprocess.Popen([KUBECTL_PATH,"get","namespaces"], stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
  namespaces = stdout.splitlines()
  if len(namespaces) > 0:
    namespaces.pop(0)      # remove first line (type of information)
  for line in namespaces:
    words = re.split(r"(\s+)",line)
    namespace = words[0]
    WildcardClusterDomain = "*.{0}{1}".format(namespace,DomainSuffix)
    WildcardClusterDomain_list.append(WildcardClusterDomain)
  
  #Request Certification for new domain(Wildcard Cluster Domain)
  NewDomain_list = list(set(WildcardClusterDomain_list).difference(set(SignedClusterDomain_list)))
  if len(NewDomain_list) > 0:
    for NewDomain in NewDomain_list:
      print('EVENT:Request Certification for '+NewDomain)
      CertbotCMD = "{0} {1} > /dev/null 2>&1".format(CertbotDNSchallenge,NewDomain)
      os.system(CertbotCMD)
      #print(CertbotCMD)
    # update New Domin to SignedClusterDomain_list
    os.system("chown -R 65534: /mnt/letsencrypt")
    SignedClusterDomain_list.extend(NewDomain_list) 

'''
### request_custom_certificate() request certificate for custom domain by using certbot webroot challenge
### and update domain information (domain, cluster-ip) to redis server.
### Domain information contain both cluster domains (e.g. <pod>.<namespace>.web.box-box.space)
### and custom domains (e.g. www.example.com, example.com)
'''
def request_custom_certificate():
  global s
  global SignedCustomDomain_list
  global DomainSuffix
  global KUBECTL_PATH
  global SERVICE_INDEX_DICT
  global EMAIL

  CertbotWebrootChallenge = "certbot certonly -n --config-dir /mnt/letsencrypt/ \
    --server https://acme-v02.api.letsencrypt.org/directory \
    --webroot --webroot-path /mnt/www/ \
    --agree-tos --non-interactive --manual-public-ip-logging-ok \
    -m {0} -d".format(EMAIL)

  #Update Cluster Domains(<pod>.<namespace>.web.box-box.space) to Redis Server
  stdout, stderr = subprocess.Popen([KUBECTL_PATH,"get","services","--all-namespaces","--show-labels","-l"
        ,"service=http"], stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
  services = stdout.splitlines()
  if len(services) > 0:
    services.pop(0)      # remove first line (type of information)
  ClusterDomain_listOfdict = []

  for line in services:
    words = re.split(r"(\s+)",line)
    namespace = words[SERVICE_INDEX_DICT['NAMESPACE']]
    podname = words[SERVICE_INDEX_DICT['NAME']]
    serviceIP = words[SERVICE_INDEX_DICT['CLUSTER-IP']]
    ClusterDomain_listOfdict.append([podname+"."+namespace+DomainSuffix,serviceIP])
  redis_set(ClusterDomain_listOfdict)
  #print("---Cluster Domain---")
  #print(ClusterDomain_listOfdict)

  #Update Custom Domains(www.example.com, example.com) to Redis Server & request custom domain certificate
  stdout, stderr = subprocess.Popen([KUBECTL_PATH,"get","services","--all-namespaces","--show-labels","-l"
        ,"service=http,domain"], stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
  services = stdout.splitlines()
  if len(services) > 0:
    services.pop(0)      # remove first line (type of information)
  CustomDomain_list = []
  CustomDomain_listOfdict = []
  for line in services:
    words = re.split(r"(\s+)",line)
    namespace = words[SERVICE_INDEX_DICT['NAMESPACE']]
    podname = words[SERVICE_INDEX_DICT['NAME']]
    serviceIP = words[SERVICE_INDEX_DICT['CLUSTER-IP']]
    label = words[SERVICE_INDEX_DICT['LABELS']]
    m = None
    m = re.match(r".*domain=([^,\n]*)", label)
    if m != None:
      domain = m.group(1)
      CustomDomain_list.append(domain)
      CustomDomain_listOfdict.append([domain,serviceIP])
  redis_set(CustomDomain_listOfdict)
  #print("---Custom Domain---")
  #print(CustomDomain_listOfdict)

  #Request Certification for new domain(Custom Domain)
  NewDomain_list = list(set(CustomDomain_list).difference(set(SignedCustomDomain_list)))
  if len(NewDomain_list) > 0:
    for NewDomain in NewDomain_list:
      print('EVENT:Request Certification for '+NewDomain)
      CertbotCMD = "{0} {1} > /dev/null 2>&1".format(CertbotWebrootChallenge ,NewDomain)
      os.system(CertbotCMD)
      #print(CertbotCMD)
    # update New Domin to SignedCustomDomain_list
    os.system("chown -R 65534: /mnt/letsencrypt")  
    SignedCustomDomain_list.extend(NewDomain_list)

### setup_service_index() get index of service information & convert to dictionary
def setup_service_index():
  global KUBECTL_PATH
  global SERVICE_INDEX_DICT
  
  SERVICE_INDEX_DICT = {}
  stdout, stderr = subprocess.Popen([KUBECTL_PATH,"get","services","--all-namespaces","--show-labels"], stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
  services = stdout.splitlines()
  services_column_name = re.split(r"(\s+)",services[0])
  column_index = 0
  for column in services_column_name:
    SERVICE_INDEX_DICT[column]=column_index
    column_index += 1
      
def main():
  global s
  global KUBECTL_PATH

  print('INITIAL: HTTP SERVICE DISCOVERY')
  while os.path.isfile(KUBECTL_PATH) == False:  #waiting for download kubectl
    #print('Downloading kubectl ...')
    time.sleep(10)
  setup_service_index()
  print('START: HTTP SERVICE DISCOVERY')
  reset_domain(86400)
  renew_custom_domain(TTL)
  renew_cluster_domain(TTL)
  s.run()

main()
