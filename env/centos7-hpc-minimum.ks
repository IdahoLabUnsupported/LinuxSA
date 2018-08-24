# Use with CentOS 7

# Kickstart Options Section
install
text
reboot

url --url=http://remote/install/path
lang en_US.UTF-8
keyboard us
skipx

network --onboot yes --device enp0s3 --bootproto dhcp --noipv6

rootpw  --iscrypted ENCRYPTEDPASSWORD

firewall --disabled

#get automounts from ldap
#authconfig --update --enableshadow --enableldap --ldapserver=LDAPSERVER --ldapbasedn=dc=my,dc=domain,dc=com --enableldapauth --enableldaptls --enablecache --enablerfc2307bis --disablesssd --disablesssdauth

selinux --disabled
timezone --utc America/Boise
bootloader --location=mbr --driveorder=sda --append="crashkernel=auto"

firstboot --disabled
zerombr
clearpart --all --drives=sda --initlabel
part swap --fstype=swap --asprimary --size=2000
part / --fstype=ext4 --asprimary --size=16000 --grow

repo --name="CentOS" --baseurl=http://remote/install/path --cost=100
repo --name="CentOS Updates" --baseurl=http://remote/install/path --cost=100

# Packages Section
#%packages --nobase --excludedocs
%packages --nobase
openssh-clients
openssh-server
pam_ldap
vim-enhanced
wget
yum
-iwl*firmware
%end

# Pre-installation Script Section
#%pre
#%end

# Post-installation Script Section>
%post --log=/root/ks-post.log

mkdir /usr/local/home
useradd -d /usr/local/home/ansible ansible
echo "ansible ALL=(root) NOPASSWD:ALL" | tee -a /etc/sudoers.d/ansible
echo "Defaults:ansible !requiretty" | tee -a /etc/sudoers.d/ansible
chmod 0440 /etc/sudoers.d/ansible
### Create ansible user ###############################################################
mkdir /usr/local/home/ansible/.ssh
chmod 700 /usr/local/home/ansible/.ssh
wget -O /usr/local/home/ansible/.ssh/authorized_keys http://remote/public/key
chown -R ansible:ansible /usr/local/home/ansible/.ssh
#######################################################################################

%end
