# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant::Config.run do |config|

  # Every Vagrant virtual environment requires a box to build off of.
  config.vm.box = "precise32"
  config.vm.box_url = "http://files.vagrantup.com/precise32.box"

  config.vm.forward_port 80, 6060

  config.vm.share_folder "share", "/usr/local/staterep/app", ".", :create => true

  config.vm.provision :shell, :path => "scripts/bootstrap.sh"

end
