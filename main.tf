variable "ssh_public_key" {
  type = string
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_instance" "instance" {
  ami = "ami-0c23cde8a0327630f"
  instance_type = "c6a.8xlarge"
  key_name = resource.aws_key_pair.ssh_key.key_name
  security_groups = [aws_security_group.ssh_ingress_all_egress.name]
  associate_public_ip_address = true

  root_block_device {
    volume_type = "gp2"
    volume_size = 200
  }
}

resource "aws_key_pair" "ssh_key" {
  key_name = "ssh_key"
  public_key = var.ssh_public_key
}


resource "aws_security_group" "ssh_ingress_all_egress" {
  name = "ssh_ingress_all_egress"
  description = "Allow ssh inbound and all outbound traffic"

  vpc_id = aws_default_vpc.default_vpc.id

  ingress {
    from_port = 22
    to_port = 22
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # allow all SSH traffic
  }

  egress { # allow all outbound traffic on all ports
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "allow_ssh"
  }
}

resource "aws_default_vpc" "default_vpc" {}

output "public_ip" {
  value = aws_instance.instance.public_ip
}
