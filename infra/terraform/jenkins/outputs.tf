# Jenkins Outputs
output "jenkins_controller_instance_id" {
  description = "Jenkins controller EC2 instance ID"
  value       = aws_instance.jenkins_controller.id
}

output "jenkins_controller_private_ip" {
  description = "Jenkins controller private IP"
  value       = aws_instance.jenkins_controller.private_ip
}

output "jenkins_controller_public_ip" {
  description = "Jenkins controller public IP"
  value       = aws_instance.jenkins_controller.public_ip
}

output "jenkins_url" {
  description = "Jenkins URL (HTTP)"
  value       = aws_instance.jenkins_controller.public_dns != "" ? "http://${aws_instance.jenkins_controller.public_dns}:8080" : "http://${aws_instance.jenkins_controller.private_ip}:8080"
}

output "jenkins_agent_launch_template_id" {
  description = "Launch template ID used for ephemeral Jenkins agents"
  value       = aws_launch_template.jenkins_agents.id
}

output "jenkins_agent_asg_name" {
  description = "Auto Scaling Group name used by Jenkins plugin for ephemeral agents"
  value       = aws_autoscaling_group.jenkins_agents.name
}

output "jenkins_plugin_hint" {
  description = "Plugin setup hint for EC2 Fleet"
  value       = "Install/configure EC2 Fleet plugin in Jenkins and target ASG: ${aws_autoscaling_group.jenkins_agents.name}"
}
