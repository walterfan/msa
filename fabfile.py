from fabric.api import *
from fabric.context_managers import *
from fabric.contrib.console import confirm 
import os, subprocess


local_dir = os.getcwd()

backend_service_ports={
"tomcat": "8080",
"kanban": "8080",
"cassandra": "9042",
"elasticsearch": "9200 9300",
"influxdb": "8086",
"postgres": "5432",
"rabbitmq": "4369 5671 5672 15671 15672 25672",
"redis": "6379",
"riak": "8087 8098",
"kafka-zookeeper": "2181 9092"
}

need_print_cmd=True
only_display_cmd=False

docker_image_prefix="walterfan-"
docker_container_prefix="msa-"

restart_policy="--restart always"
jenkins_volume_mapping = "/home/walter/workspace/jenkins:/var/jenkins_home"
jenkins_container_name="jenkins"
jenkins_image_name="walterfan-jenkins"

def run_cmd(cmd):
	if(need_print_cmd):
		print cmd
	if not only_display_cmd:
		local(cmd)


@task
def jenkins_build():
	docker_build("jenkins")

@task
def jenkins_run(listen_port="1980"):
	cmd = "docker run %s -v %s -p %s:8080 -p 50000:50000 --name=%s -d %s" % (restart_policy, jenkins_volume_mapping, listen_port, jenkins_container_name, jenkins_image_name)
	run_cmd(cmd)


@task
def jenkins_start():
	cmd = "docker start %s" % jenkins_container_name
	run_cmd(cmd)

@task
def jenkins_stop():
	cmd = "docker stop %s" % jenkins_container_name
	local(cmd)
	#cmd = "docker cp jenkins-container:/var/log/jenkins/jenkins.log jenkins.log"
	#local(cmd)

@task
def jenkins_remove():
	docker_remove(jenkins_container_name)

@task
def jenkins_commit(message):
	cmd = "docker commit -m \"%s\" %s walterfan/jenkins:1.0" % (message, jenkins_container_name)

@task
def jenkins_check():
	cmd = "docker exec %s ps -ef | grep java" % jenkins_container_name
	print cmd
	local(cmd)

	cmd = "docker exec %s cat /var/jenkins_home/secrets/initialAdminPassword" % jenkins_container_name
	print cmd
	local(cmd)

#-----------------------------------------------------------#
@task
def start_services():
	cmd = "docker-compose up -d"
	run_cmd(cmd)

@task
def stop_services():
	cmd = "docker-compose down -v"
	run_cmd(cmd)
#----------------------------- general command ----------------
def get_container_id(container_name):
	str_filter = "-aqf name=%s" % container_name;
	arr_cmd = ["docker", "ps", str_filter]
	container_id = subprocess.check_output(arr_cmd).strip()
	return container_id

def get_port_args(service_name="kanban", increment=0):
	str_port = ""
	ports = backend_service_ports[service_name]
	if ports:
		arr_port = ports.split("\\s")
		for port in arr_port:
			str_port = str_port + "-p %s:%d" %(port, int(port) + int(increment))
	return str_port

@task
def kanban_build(service_name="kanban"):
	code_dir = "examples/%s" % service_name
	container_id = get_container_id(service_name)
	with lcd(code_dir):
		local("git pull origin master")
		local("mvn package")
		local("docker cp ./target/%s*.war ../../web/apps/%s.war" % (service_name, service_name))


@task
def docker_build(service_name="tomcat"):
	docker_image_name = docker_image_prefix + service_name
	cmd = "docker build --tag %s docker/%s" % (docker_image_name, service_name)
	run_cmd(cmd)


@task
def docker_run(service_name="tomcat", volume_args="-v /workspace:/workspace"):
	port_args = get_port_args(service_name)
	
	docker_container_name = docker_container_prefix + service_name
	docker_image_name = docker_image_prefix + service_name

	cmd = "docker run %s %s %s -d --name %s %s" % (restart_policy, volume_args, port_args, docker_container_name, docker_image_name)
	run_cmd(cmd)

@task
def docker_stop(container_name="tomcat"):
	cmd = "docker stop %s" % (container_name)
	run_cmd(cmd)

@task
def docker_list(container_name="tomcat"):
	cmd = "docker ps %s" % (container_name)
	run_cmd(cmd)

@task
def docker_exec(container_name="tomcat", instruction="/bin/bash"):

	contain_id = get_container_id(container_name)
	instruction = "/bin/bash"
	cmd = "docker exec %s -t -i %s" % (contain_id, 	instruction)
	run_cmd(cmd)

@task
def docker_remove(container_name="kanban"):
	cmd1 = "docker kill %s|| true" % container_name
	run_cmd(cmd1)

	cmd2 = "docker rm -v %s || true" % container_name
	run_cmd(cmd2)

@task
def docker_commit(container_id, image_name, message=""):
	cmd = "docker commit -m \"%s\" %s %s" % (message, container_id, image_name)
	run_cmd(cmd)

@task
def docker_install():
	#cmd  ="brew remove docker && brew upgrade"
	cmd = "brew cask install docker && open /Applications/Docker.app"
	run_cmd(cmd)    

