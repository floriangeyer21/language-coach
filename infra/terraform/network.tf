# Cost-optimized network (no NAT / no VPC connector).
# RDS is publicly reachable (credential-protected) so App Runner's default public
# egress can reach it directly, alongside OpenAI. Two public subnets in different
# AZs are required for the RDS subnet group.
#
# NOTE: this trades isolation for ~$32/mo saved (no NAT gateway). RDS is protected
# by a strong generated password (and, as a follow-up, TLS). To restore full
# isolation, reintroduce private subnets + NAT + an App Runner VPC connector.

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "${var.project}-vpc" }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${var.project}-igw" }
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  tags                    = { Name = "${var.project}-public-${count.index}" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = { Name = "${var.project}-public-rt" }
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# RDS security group. App Runner's public egress IPs are not fixed, so 3306 is
# open network-wide; access is gated by the DB credentials. Narrow db_allowed_cidr
# if you later pin egress (e.g. reintroduce a VPC connector).
resource "aws_security_group" "rds" {
  name        = "${var.project}-rds"
  description = "RDS MySQL access"
  vpc_id      = aws_vpc.main.id
  ingress {
    description = "MySQL"
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = [var.db_allowed_cidr]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "${var.project}-rds-sg" }
}
