"""
Copyright 2016-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at

http://aws.amazon.com/apache2.0/

or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
"""
class Cidrblock(object):
    def __init__(self, cidr_block):
        """
        Create a Cidrblock object given a CIDR Block
        """
        if cidr_block:
            address, prefix = cidr_block.split("/")
        self.cidr_block = cidr_block
        self.address = address
        self.prefix = prefix
        self.hosts = self.get_prefix_as_decimal()

        self.broadcast = self.get_broadcast_address()
        self.network = self.get_network_address()
        self.next_block = self.get_next_cidr_block()

    def ip_to_num(self, ip):
        """
        Given an IP address return it as a decimal number
        """
        ip = ip.split(".")
        num = 0
        for i in range(4):
            num = num + int(ip[3 - i]) * (256 ** i)
        return num

    def num_to_ip(self, num):
        """
        Given a decimal number convert into IP address notation
        """
        ip = [0, 0, 0, 0]

        for i in range(4):
            ip[i] = str(num // (256 ** (3 - i)))
            num = num % (256 ** (3 - i))

        return ".".join(ip)

    def get_network_address(self):
        """
        Return the lowest decimal number of a CIDR block, 
        also known as the network address
        """
        decimal_address = self.ip_to_num(self.address)
        return decimal_address

    def get_broadcast_address(self):
        """
        Return the highest decimal number of a CIDR block,
        also known as the broadcast address
        """
        decimal_address = self.ip_to_num(self.address)
        return decimal_address + self.hosts - 1

    def get_prefix_as_decimal(self):
        """
        Return the decimal number of the amount of IP addresses in a prefix
        Ex. /24 is 256, /16 is 65536
        """
        print self.prefix
        print type(self.prefix)
        n = 32 - int(self.prefix)
        addresses = 2 ** n
        return addresses

    def get_next_cidr_block(self):
        """
        Return the next CIDR block
        """
        next_block = self.num_to_ip(self.broadcast + 1)
        str_next_block = "{}/{}".format(str(next_block), str(self.prefix))
        return str_next_block

class VpcRange(object):
    def __init__(self, vpc_cidr_block, subnets):
        """
        Create a VPC object that has subnets
        """
        vpc = Cidrblock(vpc_cidr_block)

        self.vpc_cidr_block = vpc_cidr_block    # Ex: 192.168.0.0/16
        self.address = vpc.address              # Ex: 192.168.0.0
        self.prefix = vpc.prefix                # Ex: 16
        self.hosts = vpc.hosts                  # Ex: 65536
        self.highest = vpc.broadcast            # Ex: 192.168.255.255
        self.lowest = vpc.network               # Ex: 192.168.0.0

        self.subnet_list = []

        for subnet in subnets:
            s = Cidrblock(subnet)
            self.subnet_list.append(s)

    def add_subnet(self, new):
        """
        Add subnet to object's subnet list
        """
        new_subnet = Cidrblock(new)
        self.subnet_list.append(new_subnet)

    def compare_subnets(self, current, new):
        """
        Given a subnet compare with a VPC subnet and determine if they overlap
        return True
        """
        if is_address_within_network(new.network, current):
            return True
        elif is_address_within_network(new.broadcast, current):
            return True
        else:
            return False

    def within_vpc(self, new):
        """
        Given a new subnet return True if its within the VPC Network Block
        """
        if (new.network > self.highest) and (new.network < self.lowest):
            return False
        elif (new.broadcast > self.highest) or (new.broadcast < self.lowest):
            return False
        return True

    def vet_subnet(self, new):
        """
        Given a new subnet check to ensure that it's within the VPC and that it
        doesn't overlap with another subnet
        """
        new_subnet = Cidrblock(new)
        if not self.within_vpc(new_subnet):
            return (False, "Not within VPC network")
        overlap = False
        for current_subnet in self.subnet_list:
            if self.compare_subnets(current_subnet, new_subnet) and not overlap:
                overlap = (True, new_subnet.next_block)
        if overlap:
            return (True, new_subnet.next_block)
        else:
            self.add_subnet(new)
            return (False, new_subnet.cidr_block)

    def get_subnet_list(self):
        """
        Return readable subnet list
        """
        subnet_list = []
        for subnet in self.subnet_list:
            subnet_list.append(subnet.cidr_block)
        return subnet_list

    def is_address_within_network(self, ip_address, current):
        """
        Given an IP address and network range determine if it lies within a network
        """
        network_address = current.network
        broadcast_address = current.broadcast
        if ((ip_address >= network_address) and (ip_address <= broadcast_address)):
            return True
        return False

class Prefix(object):
    """
    Create a prefix block that will return the first available CIDR Block
    in a VPC
    """
    def __init__(self, prefix, vpc):
        """
        Given a prefix (string) and vpc (VpcRange object) determine
        next available cidr block in a VPC
        """
        print "Prefix class run.  Prefix is: {}".format(prefix)
        self.vpc = vpc
        self.prefix = prefix

        first_ip = self.get_first_vpc_ip()
        cidr_block = self.get_cidr_block(first_ip)

        self.first_available = self.get_available_block(cidr_block)

    def get_first_vpc_ip(self):
        """
        Return VPC network address as string
        """
        first_block = self.vpc.address
        return first_block

    def get_cidr_block(self, network):
        """
        Given a network return the cidr block
        """
        cidr_block = "{}/{}".format(network, self.prefix)
        return cidr_block

    def get_available_block(self, cidr_block):
        """
        Given a starting CIDR block loop through a VPC 
        until a free block is found
        """
        while self.vpc.vet_subnet(cidr_block)[0]:
            cidr_block = self.vpc.vet_subnet(cidr_block)[1]
        return cidr_block


