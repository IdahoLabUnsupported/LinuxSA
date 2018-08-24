
function get_tools_versions () {
  RELEASE_STRING=`cat /etc/*release* 2>&1`

  if [[ $RELEASE_STRING =~ CentOS.*release[[:space:]]+([\.[:digit:]]+) ]] ; then
    REV="${BASH_REMATCH[1]}"
    if [[ $REV =~ ^5 ]] ; then
      PERLBREW_REV='centos_5_7_glibc_2_5_123'
      py_revs[0]='python_centos_5_7_glibc_2_5_123'
      py_revs[1]='python3_centos_5_7_glibc_2_5_123'
    elif [[ $REV =~ ^6 ]] ; then
      PERLBREW_REV='centos_6_7_glibc_2_12_1_166'
      py_revs[0]='python_centos_6_8_glibc_2_12_1_192'
      py_revs[1]='python3_centos_6_8_glibc_2_12_1_192'
    elif [[ $REV =~ ^7 ]] ; then
      PERLBREW_REV='centos_7_2_151_glibc_2_17_106'
      py_revs[0]='python_centos_7_2_glibc_2_17_106'
      py_revs[1]='python3_centos_7_2_glibc_2_17_106'
    else
      PERLBREW_REV='centos_6_7_glibc_2_12_1_166'
      py_revs[0]='python_centos_6_8_glibc_2_12_1_192'
      py_revs[1]='python3_centos_6_8_glibc_2_12_1_192'
    fi  
  elif [[ $RELEASE_STRING =~ Red[[:space:]]+Hat[[:space:]]+Enterprise.*release[[:space:]]+([\.[:digit:]]+) ]] ; then
    REV="${BASH_REMATCH[1]}"
    if [[ $REV =~ ^5 ]] ; then
      PERLBREW_REV='centos_5_7_glibc_2_5_123'
      py_revs[0]='python_centos_5_7_glibc_2_5_123'
      py_revs[1]='python3_centos_5_7_glibc_2_5_123'
    elif [[ $REV =~ ^6 ]] ; then
      PERLBREW_REV='centos_6_7_glibc_2_12_1_166'
      py_revs[0]='python_centos_6_8_glibc_2_12_1_192'
      py_revs[1]='python3_centos_6_8_glibc_2_12_1_192'
    elif [[ $REV =~ ^7 ]] ; then
      PERLBREW_REV='centos_7_2_151_glibc_2_17_106'
      py_revs[0]='python_centos_7_2_glibc_2_17_106'
      py_revs[1]='python3_centos_7_2_glibc_2_17_106'
    else
      PERLBREW_REV='centos_6_7_glibc_2_12_1_166'
      py_revs[0]='python_centos_6_8_glibc_2_12_1_192'
      py_revs[1]='python3_centos_6_8_glibc_2_12_1_192'
    fi 
  elif [[ $RELEASE_STRING =~ SUSE.*Server[[:space:]]+([\.[:digit:]]+) ]] ; then
    REV="${BASH_REMATCH[1]}"
    if [[ $REV =~ ^11 ]] ; then
      PERLBREW_REV='suse_11_3_glibc_2_11_3_17'
      py_revs[0]='python_suse_11_4_glibc_2_11_3_17'
      py_revs[1]='python3_suse_11_4_glibc_2_11_3_17'
    elif [[ $REV =~ ^12 ]] ; then
      PERLBREW_REV='suse_11_3_glibc_2_11_3_17'
      py_revs[0]='python_suse_12_3_glibc_2_2_62'
      py_revs[1]='python3_suse_12_3_glibc_2_2_62'
    else
      PERLBREW_REV='use_11_3_glibc_2_11_3_17'
      py_revs[0]='python_suse_11_4_glibc_2_11_3_17'
      py_revs[1]='python3_suse_11_4_glibc_2_11_3_17'
    fi 
  elif [[ $RELEASE_STRING =~ Ubuntu.*[[:space:]]+([\.[:digit:]]+) ]] ; then
    REV="${BASH_REMATCH[1]}"
    if [[ $REV =~ ^14 ]] ; then
      PERLBREW_REV='ubuntu_14_04_3_glibc_2_19_1'
      py_revs[0]='python_ubuntu_14_04_3_glibc_2_19_1'
      py_revs[1]='python3_ubuntu_14_04_3_glibc_2_19_1'
    else
      PERLBREW_REV='ubuntu_14_04_3_glibc_2_19_1'
      py_revs[0]='python_ubuntu_14_04_3_glibc_2_19_1'
      py_revs[1]='python3_ubuntu_14_04_3_glibc_2_19_1'
    fi 
  fi
}


if [ -z ${PERLBREW_VERSION+x} ] ; then
  get_tools_versions
  if [ -f /path/to/bin/perlbrew ] ; then
    source /path/to/etc/bashrc
    perlbrew use $PERLBREW_REV
  fi
fi

if [ -z ${PYENV_VERSION+x} ] ; then
  get_tools_versions
  if [ -f /path/to/bin/pyenv ] ; then
    export PYENV_ROOT="/path/to/pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
    pyenv shell ${py_revs[@]}
  fi
fi

