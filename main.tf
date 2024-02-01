variable "ssh_public_key" {
  type = string
  nullable = false
}

variable "ssh_private_key" {
  type = string
  sensitive = true
  nullable = false
}


variable "region" {
  type = string
  default = "us-east-1"
  nullable = false
}

provider "aws" {
  region = var.region
}

resource "aws_instance" "instance" {
  ami = module.ami.ami
  instance_type = "c6a.8xlarge"
  key_name = resource.aws_key_pair.ssh_key.key_name
  security_groups = [aws_security_group.ssh_ingress_all_egress.name]
  associate_public_ip_address = true

  root_block_device {
    volume_type = "gp2"
    volume_size = 200
  }
}

module "ami" {
  source = "github.com/Gabriella439/terraform-nixos-ng//ami"
  release = "23.05"
  region = var.region
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

module "deploy_nixos" {
  source = "github.com/nix-community/terraform-nixos//deploy_nixos?ref=646cacb12439ca477c05315a7bfd49e9832bc4e3"
  flake = true
  nixos_config = "default"
  hermetic = true
  target_user = "root"
  target_host = aws_instance.instance.public_ip
  ssh_private_key = var.ssh_private_key
}

resource "null_resource" "wait_for_ssh_access" {
  # This ensures that the instance is reachable via `ssh` before we deploy NixOS
  provisioner "remote-exec" {
    connection {
      host = aws_instance.instance.public_dns
      private_key = var.ssh_private_key
    }

    inline = [ ":" ]
  }
}

output "public_ip" {
  value = aws_instance.instance.public_ip
}
