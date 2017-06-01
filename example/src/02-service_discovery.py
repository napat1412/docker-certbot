import sched, time
import subprocess, re, os

s = sched.scheduler(time.time, time.sleep)
CheckNewDomain_sched = 0
RenewedDomain_list = []

### renew_domain() set for renew all active domain everydays 
def renew_domain_daily(OffsetTime=86400):
  global s
  global RenewDomainMinutely_sched
  global RenewedDomain_list

  print("EVENT:renew domain")

  ### Remove schedule: RenewDomainMinutely
  if s.empty()== False :
    s.cancel(RenewDomainMinutely_sched)

  ### Reset variable:RenewedDomain_list to force certificate-request for all domain daily
  RenewedDomain_list = []
  request_certificate()

  ### re-schedule check_new_domain()
  now = time.time()
  RenewDomainMinutely_sched = s.enterabs(now+1, 0, renew_domain_minutely, ())
  s.enterabs(now+OffsetTime, 0, renew_domain_daily, (86400,))

def renew_domain_minutely(OffsetTime=60):
  global s
  global RenewDomainMinutely_sched

  #print("EVENT:renew_domain_minutely")
  request_certificate()
  now = time.time()
  RenewDomainMinutely_sched = s.enterabs(now+OffsetTime, 0, renew_domain_minutely, ())

def request_certificate():
  global s
  global RenewedDomain_list

  CertbotCMDPrefix = "certbot certonly -n --webroot --webroot-path /mnt/www/ --config-dir /mnt/letsencrypt/ \
     -m napat.chu@gmail.com --agree-tos -d "
  KUBECTL_PATH="/usr/local/bin"

  p = subprocess.Popen([KUBECTL_PATH+"/kubectl","get","services","--all-namespaces","-l","service=http"]
        ,stdout=subprocess.PIPE)
  result = p.stdout.read()

  pods = result.decode("utf-8")
  linenumber = 0
  CurrentDomain_list = []

  for line in pods.splitlines():
    if linenumber > 0:
      words = re.split(r"(\s+)",line)
      namespace = words[0]
      podname = words[2]
      CurrentDomain_list.append(podname+"."+namespace+".w3.8app.cf")
    linenumber += 1
  NewDomain_list = list(set(CurrentDomain_list).difference(set(RenewedDomain_list)))

  if len(NewDomain_list) > 0:
    for NewDomain in NewDomain_list:
      print('EVENT:Request Certification for '+NewDomain)
      CertbotCMD = "{0}{1} > /dev/null 2>&1".format(CertbotCMDPrefix,NewDomain)
      #os.system(CertbotCMD)
      #print(CertbotCMD)
  
    os.system("chown -R 65534: /mnt/letsencrypt")  
    RenewedDomain_list.extend(NewDomain_list)


def main():
  global s

  print('START: HTTP SERVICE DISCOVERY')
  time.sleep(60)                              #wait for install kubectl
  renew_domain_daily()
  s.run()

main()
