#!/usr/bin/python
### author : Kami Gerami
### This script will setup a new ghost instance under /var/www/domain/nameofyourblog
### it will create a nginx conf file under /etc/nginx/sites-enabled/nameofyourblog.domain
### it requires template files to be placed under /opt/projects/subtemp.template/{etc,var}
import time
import web
import socket
import shutil
import os
import MySQLdb
import sys
import fileinput
import subprocess
import string
import random
urls = (
    '/', 'index'
)

def createGhostInstance():
  global subtemp
  global port
  global uid
  global user
  global domain
  ipaddr = '127.0.0.1' #localhost
  def PickUnusedPort():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    addr, port = s.getsockname()
    s.close()
    return port
  # set the port from the function to var port
  port = PickUnusedPort() # set random port same as UID in db
  uid = port
   # first get the name of the latest DB that was created via website and set it to var subtemp
  sqluser = 'root' #main sql user
  sqlpw = '/root/.sqlpw' # main sql pw

  db = MySQLdb.connect(host="localhost", user=sqluser, read_default_file=sqlpw, db="register_db")
   
  cursor = db.cursor()
  
  latest_unassigned_user = "select name from unassigned_users order by created_at DESC limit 1"
  
   # execute SQL select statement
  cursor.execute(latest_unassigned_user)
   
   # commit your changes
  db.commit()
   
   # get the number of rows in the resultset
  numrows = int(cursor.rowcount)
   
   # get and display one row at a time.
  for x in range(0,numrows):
      row = cursor.fetchone()
      user = row[0]
      subtemp = user
  
  assign_free_uid_to_unassigned_user = "update r_lookup r, unassigned_users u set r.name = u.name, r.email = u.email where r.uid = '%s'" %(uid,)
 
  remove_unassigned_user_after_assignment = "delete from unassigned_users where name = '%s'" %(user,)

  cursor.execute(latest_unassigned_user);
  cursor.execute(assign_free_uid_to_unassigned_user);
  cursor.execute(remove_unassigned_user_after_assignment);
  #cursor.execute(insert_uid_to_r_lookup);
  db.commit()
 
 #select latest created without a name yet
 # select uid from r_lookup where name is null order by created_at DESC limit 1;
  
  domain = 'balala.se' #domain address - change if necessary
  var_src = "/opt/project/subdomain.template/var/www/%s/uid/subtemp.%s/" %(domain, domain)
  var_dst = "/var/www/%s/uid/" %domain
   
  etc_src = "/opt/project/subdomain.template/etc/nginx/sites-enabled/subtemp.%s" %domain
  etc_dst = "/etc/nginx/sites-enabled/" #nginx sites-enabled dir
  
  filetoreplacein = '' 
 
  ### create NEW database for subtemp user so GHOSt can use this
  # genereate random PW for ghost_sql user
  char_set = string.ascii_uppercase + string.digits
  ghost_sql_pw = ''.join(random.sample(char_set*8, 8))
 
  # change DB name here from balala to whatever you wanna call it manually if name is not satisfactory
  cursor.execute("create database if not exists uid_%s" %uid)
  cursor.execute("grant create,delete,insert,select,update,alter on uid_%s.* to 'user_%s'@'localhost'" %(uid, uid) )
  cursor.execute("set password for 'user_%s'@'localhost' = PASSWORD('%s')" %(uid, ghost_sql_pw) )
  db.commit()
  
  # add subtemp (blogname from DB to end of dst path)
 
  var_dst = var_dst + str(uid)
  etc_dst = etc_dst + subtemp + "." + domain
  
  ########### DEFINING FUNCTIONS BELOW  ###############
  ##########                             ##############
  #####################################################
 
      #shutil.copy(src, dst) will copy /etc/nginx/sites-available/subtemp.domain.se
  def cpfile_etc(etc_src, etc_dst):
      shutil.copy(etc_src, etc_dst)
  
  #this function will replace subtemp with blogname created inside of filetoreplacein 
  def edit_subtemp(filetoreplacein):
      for linesubtemp in fileinput.FileInput(filetoreplacein,inplace=1):
          linesubtemp = linesubtemp.replace("subtemp",subtemp)
          print linesubtemp
   
  def edit_uid(filetoreplacein):
      for lineuid in fileinput.FileInput(filetoreplacein,inplace=1):
          lineuid = lineuid.replace("subtemp",uid)
          print lineuid
   
#this function will replace portnumber with port in file.
  def edit_portnumber(filetoreplacein):
      for lineport in fileinput.FileInput(filetoreplacein,inplace=1):
          lineport = lineport.replace("portnumber", "%s" %port)
          print lineport
 
  #this function will replace sql_pw that was generated inside filetoreplacein
  def edit_ghost_sql_pw(filetoreplacein):
      for sql_pw in fileinput.FileInput(filetoreplacein,inplace=1):
          sql_pw = sql_pw.replace("ghost_sql_pw", "%s" %ghost_sql_pw)
          print sql_pw
 
  #this function will run a command that is given in cmd var
  def runcommand(cmd):
  	p = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE)
  	while True:
      	    out = p.stderr.read(1)
      	    if out == '' and p.poll() != None:
              break
      	    if out != '':
              sys.stdout.write(out)
      	      sys.stdout.flush()
 
  #this function will clean upp all whitespace in files
  def edit_clean_whitespace(filetoreplacein):
      with open(filetoreplacein,"r") as f:
          lines=f.readlines()
 
      with open(filetoreplacein,"w") as f:
          [f.write(line) for line in lines if line.strip() ]
 
  #################################################
  #############    SANITY CHECKS     ##############
  #################################################
   
  # if the path already exists for /etc/nginx/sites-enabled/subtemp.domain.se raise Exception otherwise copy file
  if os.path.exists(etc_dst):
      raise Exception ('A sites-enabled file already exists for %s.' %etc_dst)
  else:
      cpfile_etc(etc_src, etc_dst);
   
  #####################################################
  ###########  CALLING FUNCTIONS BELOW  ###############
  ##########                             ##############
  #####################################################
  
  # start with editing the subtemp var inside /etc/nginx/sites-enabled/subtemp.domain.se file
  edit_subtemp(etc_dst);
  # edit portnumber inside the /etc/nginx/sites-enabled/subtemp.domain.se file 
  edit_portnumber(etc_dst);
 
  # create var for config.js file under /var/www/... 
  var_dst_configjs = var_dst + "/" + "config.js"
  
  if os.path.exists(var_dst_configjs):
      # change subtemp variable in config.js file
      edit_uid(var_dst_configjs);
      # change portnumber variable in config.js file
      edit_portnumber(var_dst_configjs);
      # add new ghost_users sql password to config.js file
      edit_ghost_sql_pw(var_dst_configjs);
 
  #create SYMLINK from UID to subtemp
  symlink_src = "/var/www/%s/uid/%s" %(domain, uid)
  symlink_dst = "/var/www/%s/name/%s" %(domain, subtemp)
  os.symlink(symlink_src, symlink_dst)
  
  # add info to /etc/hosts
  
  try:
      # This tries to open an existing file but creates a new file if necessary.
      logfile = open("/etc/hosts", "a")
      try:
          logfile.write('\n%s %s.%s %s' %(ipaddr, subtemp, domain, subtemp))
      finally:
          logfile.close()
  except IOError:
      pass
  
  
  # reload nginx
  
  print "Reloading nginx"
  ## run it ##
  runcommand("/etc/init.d/nginx reload");
   
  def cpdir_var(var_src, var_dst):
    shutil.copytree(var_src, var_dst)
  cpdir_var(var_src, var_dst)
 
  # this command will change dir to /var/www/domain.se/subtemp/ and run npm install to setup ghost / nodejs
  #change dir to the newly created dir
  os.chdir(var_dst) #dst + uid
  # run install command
  runcommand("/usr/bin/npm start");
  # then start pm2 instance
  runcommand("NODE_ENV=production /usr/bin/pm2 start index.js --name '%s.%s' -f" %(subtemp, domain));
 
  # clean upp all whitespace in files
  edit_clean_whitespace(var_dst_configjs);
  edit_clean_whitespace(etc_dst);

def createNEWGhost():
  def PickUnusedNEWPort():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    addr, port = s.getsockname()
    s.close()
    return port
  # set the port from the function to var port
  newport = PickUnusedNEWPort()
  newport = str(newuid) # set random port same as UID in db
  var_src = "/opt/project/subdomain.template/var/www/%s/uid/subtemp.%s/" %(domain, domain)
  var_dst = "/var/www/%s/uid/" %domain
  var_dst = var_dst + newuid
#shutil.copytree(src, dst) will copy VAR PATH recursively
  def cpdir_var(var_src, var_dst):
      shutil.copytree(var_src, var_dst)
  
  # if the path already exists for /var/www/domain.se/subtemp raise Exception otherwise copy files
  if os.path.exists(var_dst):
      raise Exception ('A directory with name %s already exists.' %(var_dst))
  else:
      cpdir_var(var_src, var_dst); #dst + uid
  #insert into DB new uid
  sqluser = 'root' #main sql user
  sqlpw = '/root/.sqlpw' # main sql pw

  db = MySQLdb.connect(host="localhost", user=sqluser, read_default_file=sqlpw, db="register_db")
   
  cursor = db.cursor()
  
  insert_newuid_to_r_lookup = "insert into r_lookup (uid) VALUES ('%s')" %newuid
  
   # execute SQL select statement
  cursor.execute(insert_newuid_to_r_lookup)
   
   # commit your changes
  db.commit()
 
class index:
    def GET(self):
        createGhostInstance() 
        time.sleep(10)
        #redirect to subtemp.domain/ghost"
	url = "http://%s.%s/ghost" %(subtemp, domain)
	raise web.seeother(url)
        return "Ghost installed! - redirecting you to your personal setup page"
        createNEWGhost()
if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()