VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|


  config.vm.define "ship-container" do |v|
    v.vm.provider "docker" do |d|
      d.image = "anaderi/ocean:latest"
      d.volumes = ["/vagrant:/opt/ship"]

      d.env = {
        VAR: 'value',
      }

      d.vagrant_vagrantfile = "./vm/Vagrantfile.proxy"
      # d.remains_running = false
    end
  end
end




