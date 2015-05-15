# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure(2) do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://atlas.hashicorp.com/search.
  config.vm.box = "ubuntu/trusty64"

  # Disable automatic box update checking. If you disable this, then
  # boxes will only be checked for updates when the user runs
  # `vagrant box outdated`. This is not recommended.
  # config.vm.box_check_update = false

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  config.vm.network "forwarded_port", guest: 80, host: 5000

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  # config.vm.network "private_network", ip: "192.168.33.10"

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  # config.vm.network "public_network"

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  # config.vm.synced_folder "../data", "/vagrant_data"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:
  #
  config.vm.provider "virtualbox" do |vb|
    # Display the VirtualBox GUI when booting the machine
    # vb.gui = true
  
    # Customize the amount of memory on the VM:
    vb.memory = "2048"
  end
  #
  # View the documentation for the provider you are using for more
  # information on available options.

  # Define a Vagrant Push strategy for pushing to Atlas. Other push strategies
  # such as FTP and Heroku are also available. See the documentation at
  # https://docs.vagrantup.com/v2/push/atlas.html for more information.
  # config.push.define "atlas" do |push|
  #   push.app = "YOUR_ATLAS_USERNAME/YOUR_APPLICATION_NAME"
  # end

  # Enable provisioning with a shell script. Additional provisioners such as
  # Puppet, Chef, Ansible, Salt, and Docker are also available. Please see the
  # documentation for more information about their specific syntax and use.
  config.vm.provision "shell", inline: <<-SHELL
    sudo add-apt-repository ppa:webupd8team/java -y
    sudo apt-get update
    sudo apt-get install -y debconf-utils
    sudo debconf-set-selections <<< "oracle-java8-installer shared/accepted-oracle-license-v1-1 select true"
    sudo debconf-set-selections <<< "oracle-java8-installer shared/accepted-oracle-license-v1-1 seen true"
    sudo apt-get install -y git-core python python-dev mininet python-pip oracle-java8-installer oracle-java8-set-default maven
    
    mkdir Downloads Applications
    cd Downloads
    wget http://download.nextag.com/apache/karaf/3.0.3/apache-karaf-3.0.3.tar.gz
    tar -zxvf apache-karaf-3.0.3.tar.gz -C ../Applications/
    cd $HOME
    sudo sed -i '/^featuresRepositories=/ s/$/,mvn:org.onosproject\/onos-features\/1.2.0-SNAPSHOT\/xml\/features/' ~/Applications/apache-karaf-3.0.3/etc/org.apache.karaf.features.cfg

    git clone https://gerrit.onosproject.org/onos
    cd onos
    mvn clean install -DskipTests=true

    cd $HOME
    wget https://nexus.opendaylight.org/content/groups/public/org/opendaylight/integration/distribution-karaf/0.2.3-Helium-SR3/distribution-karaf-0.2.3-Helium-SR3.tar.gz
    tar xzf distribution-karaf-0.2.3-Helium-SR3.tar.gz

    sudo pip install ryu
  SHELL
  config.vm.provision "shell", run: "always", inline: <<-SHELL
    export ONOS_ROOT=~/onos
    source ~/onos/tools/dev/bash_profile
    export ONOS_USER=vagrant
    export ONOS_GROUP=vagrant
  SHELL
end
