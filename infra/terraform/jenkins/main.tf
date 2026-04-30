data "aws_vpc" "default" {
  default = true
}

data "aws_vpc" "jenkins" {
  id = var.jenkins_vpc_id != "" ? var.jenkins_vpc_id : data.aws_vpc.default.id
}

data "aws_subnets" "jenkins" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.jenkins.id]
  }
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

locals {
  jenkins_subnet_ids  = length(var.jenkins_subnet_ids) > 0 ? var.jenkins_subnet_ids : data.aws_subnets.jenkins.ids
  jenkins_ami_id      = var.jenkins_ami_id != "" ? var.jenkins_ami_id : data.aws_ami.ubuntu.id
  jenkins_name_prefix = "${var.project_name}-${var.environment}-jenkins"
}

resource "aws_security_group" "jenkins_controller" {
  name        = "${local.jenkins_name_prefix}-controller-sg"
  description = "Jenkins controller security group"
  vpc_id      = data.aws_vpc.jenkins.id

  ingress {
    description = "HTTP access to Jenkins UI"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = var.jenkins_controller_allowed_cidrs
  }

  ingress {
    description = "SSH access to controller"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.jenkins_controller_allowed_cidrs
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${local.jenkins_name_prefix}-controller-sg"
    Role = "jenkins-controller"
  })
}

resource "aws_security_group" "jenkins_agents" {
  name        = "${local.jenkins_name_prefix}-agents-sg"
  description = "Jenkins ephemeral agent security group"
  vpc_id      = data.aws_vpc.jenkins.id

  ingress {
    description     = "SSH from Jenkins controller"
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.jenkins_controller.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${local.jenkins_name_prefix}-agents-sg"
    Role = "jenkins-agents"
  })
}

resource "aws_iam_role" "jenkins_controller" {
  name = "${local.jenkins_name_prefix}-controller-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "${local.jenkins_name_prefix}-controller-role"
  })
}

resource "aws_iam_role_policy" "jenkins_controller_ec2fleet" {
  name = "${local.jenkins_name_prefix}-controller-policy"
  role = aws_iam_role.jenkins_controller.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "EC2Describe"
        Effect = "Allow"
        Action = [
          "ec2:Describe*",
          "autoscaling:Describe*",
          "elasticloadbalancing:Describe*"
        ]
        Resource = "*"
      },
      {
        Sid    = "ScaleJenkinsAgentAsg"
        Effect = "Allow"
        Action = [
          "autoscaling:SetDesiredCapacity",
          "autoscaling:TerminateInstanceInAutoScalingGroup"
        ]
        Resource = "*"
      },
      {
        Sid    = "SSMAndLogs"
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParameterHistory",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "jenkins_controller" {
  name = "${local.jenkins_name_prefix}-controller-profile"
  role = aws_iam_role.jenkins_controller.name
}

resource "aws_iam_role_policy_attachment" "jenkins_controller_ssm" {
  role       = aws_iam_role.jenkins_controller.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
  # NOTE: The double-colon (arn:aws:iam::aws:policy/...) is intentional for
  # AWS global IAM policies. If this fails, use:
  # policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role" "jenkins_agent" {
  name = "${local.jenkins_name_prefix}-agent-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "${local.jenkins_name_prefix}-agent-role"
  })
}

resource "aws_iam_role_policy_attachment" "jenkins_agent_ssm" {
  role       = aws_iam_role.jenkins_agent.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "jenkins_agent" {
  name = "${local.jenkins_name_prefix}-agent-profile"
  role = aws_iam_role.jenkins_agent.name
}

resource "aws_launch_template" "jenkins_agents" {
  name_prefix   = "${local.jenkins_name_prefix}-agent-lt-"
  image_id      = local.jenkins_ami_id
  instance_type = var.jenkins_agent_instance_type
  key_name      = var.jenkins_agent_key_name != "" ? var.jenkins_agent_key_name : null

  vpc_security_group_ids = [aws_security_group.jenkins_agents.id]

  iam_instance_profile {
    arn = aws_iam_instance_profile.jenkins_agent.arn
  }

  user_data = base64encode(templatefile("${path.module}/templates/jenkins-agent-user-data.sh.tftpl", {}))

  tag_specifications {
    resource_type = "instance"
    tags = merge(var.tags, {
      Name = "${local.jenkins_name_prefix}-agent"
      Role = "jenkins-agent-ephemeral"
    })
  }

  update_default_version = true
}

resource "aws_autoscaling_group" "jenkins_agents" {
  name                      = "${local.jenkins_name_prefix}-agents-asg"
  min_size                  = 0
  max_size                  = var.jenkins_agent_max_size
  desired_capacity          = 0
  health_check_type         = "EC2"
  health_check_grace_period = 120
  vpc_zone_identifier       = local.jenkins_subnet_ids

  launch_template {
    id      = aws_launch_template.jenkins_agents.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${local.jenkins_name_prefix}-agent"
    propagate_at_launch = true
  }

  tag {
    key                 = "Role"
    value               = "jenkins-agent-ephemeral"
    propagate_at_launch = true
  }

  dynamic "tag" {
    for_each = var.tags
    content {
      key                 = tag.key
      value               = tag.value
      propagate_at_launch = true
    }
  }
}

resource "aws_instance" "jenkins_controller" {
  ami                         = local.jenkins_ami_id
  instance_type               = var.jenkins_controller_instance_type
  subnet_id                   = local.jenkins_subnet_ids[0]
  vpc_security_group_ids      = [aws_security_group.jenkins_controller.id]
  iam_instance_profile        = aws_iam_instance_profile.jenkins_controller.name
  key_name                    = var.jenkins_controller_key_name != "" ? var.jenkins_controller_key_name : null
  associate_public_ip_address = var.jenkins_controller_public_ip

  user_data = templatefile("${path.module}/templates/jenkins-controller-user-data.sh.tftpl", {
    jenkins_admin_username = var.jenkins_admin_username
    jenkins_admin_password = var.jenkins_admin_password
    jenkins_agent_asg_name = aws_autoscaling_group.jenkins_agents.name
    jenkins_agent_max_size = var.jenkins_agent_max_size
    aws_region             = var.aws_region
  })

  root_block_device {
    volume_size = var.jenkins_controller_root_volume_size
    volume_type = "gp3"
    encrypted   = true
  }

  tags = merge(var.tags, {
    Name = "${local.jenkins_name_prefix}-controller"
    Role = "jenkins-controller"
  })
}
