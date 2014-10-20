VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.define "ship-container", primary: true do |v|
    v.vm.provider "docker" do |d|
      d.image = "anaderi/ocean:latest"
      d.volumes = ["/vagrant:/opt/ship"]
      d.vagrant_vagrantfile = "./Vagrantfile"
      d.vagrant_machine = "proxy"
      d.remains_running = false
    end
  end

  config.vm.define "proxy", autostart: false do |proxy|
    proxy.vm.box = "yungsang/boot2docker"
    proxy.vm.provision "docker"
    proxy.vm.network "private_network", ip: "192.168.33.10"
    proxy.vm.synced_folder ".", "/vagrant", type: "nfs"
    proxy.vm.network :forwarded_port, guest: 5900, host: 6900
    proxy.vm.provision "shell", inline:
	"sudo ntpclient -s -h time.nist.gov"
    config.vm.provider "virtualbox" do |vb|
      vb.memory = 1024
      vb.cpus = 1
    end
  end
end
