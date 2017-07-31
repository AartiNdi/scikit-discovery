import re
import socket
import time
import psutil
import boto3
import subprocess
import psutil
from skdiscovery.utilities import config
from paramiko.ssh_exception import SSHException

from collections import OrderedDict
import random
import string
from skdiscovery.utilities.ssh_reverse import ReverseTunnel


aws_access_key = None
aws_secret = None
aws_region = None
aws_security_group = None
aws_key_name = None
pem_file = None
ec2_res = None
ec2_client = None
amazon_list = []
scheduler = None
popen = None


def init(in_aws_access_key, in_aws_secret, in_aws_region, in_aws_security_group, in_aws_key_name, in_pem_file):
    '''
    The underlying functionality for the Amazon GUI, the user should not need to directly interface with this function

    @param in_aws_access_key: AWS access key
    @param in_aws_secret: AWS Secret Access Key
    @param in_aws_region: AWS region (e.g. us-west-2)
    @param in_aws_security_group: Security Group Name
    @param in_aws_key_name: Name of Key Pair
    @param in_pem_file: Filename of ssh key
    '''    

    global aws_access_key
    global aws_secret
    global aws_region
    global aws_security_group
    global aws_key_name
    global pem_file
    global ec2_res
    global ec2_client
    global amazon_list
    
    aws_access_key = in_aws_access_key
    aws_secret = in_aws_secret
    aws_region = in_aws_region
    aws_security_group = in_aws_security_group
    aws_key_name = in_aws_key_name
    pem_file = in_pem_file
    ec2_res =  boto3.resource('ec2', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret,
                              region_name=aws_region)

    ec2_client = boto3.client('ec2', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret,
                              region_name=aws_region)


    clearAmazonList()

    full_info = ec2_client.describe_instances()

    for reservation in full_info['Reservations']:
        for instance in reservation['Instances']:
            if 'Tags' in instance:
                if re.search('^CAD_Cloud_i-[0-9a-zA-Z]*', instance['Tags'][0]['Value']):
                # if re.search('^scale1.*', instance['Tags'][0]['Value']):
                    instance_obj = ec2_res.Instance(id=instance['InstanceId'])
                    new_instance = generateInfo(instance_obj)
                    if new_instance['state'] in ('running','pending'):
                        amazon_list.append(new_instance)

    if len(amazon_list) > 0:
        resetInstances()
        createTunnels()
        startDispyNode()        
        startDispyScheduler()
        

def closeDispyScheduler():
    ''' Close the Dispy Scheduler '''

    global popen
    if popen != None:
        popen.terminate()
        popen.wait()
        popen=None

    else:
        for proc in psutil.process_iter():
            try:
                cmdline = proc.cmdline()
            except (PermissionError, psutil.AccessDenied):
                continue

            for arg in cmdline:
                if re.search('dispyscheduler.py',arg):
                    proc.send_signal(psutil.signal.SIGTERM)
    
def startDispyScheduler():
    ''' Start the Dispy Scheduler '''

    closeDispyScheduler()

    dispy_pass = config.getDispyPassword()    

    global popen
    
    args = ['dispyscheduler.py', '--node_secret', dispy_pass, '--ext_ip_addr',
            '127.0.0.1', '--cluster_secret', dispy_pass, '--pulse_interval',
            '60','--daemon','--msg_timeout', '60', '--httpd']

    for info in amazon_list:
        args.append('-n')
        args.append(info['ip_address'])

    popen =  subprocess.Popen(args, shell=False)
    

def generateInfo(instance):
    '''
    Read metadata from an Amazon instance

    @return metadata for Amazon instance
    '''
    new_info = OrderedDict()
    new_info['amazon_id'] = instance.id
    new_info['state'] = instance.state['Name']
    new_info['tunnel'] = None
    new_info['ip_address'] = instance.public_ip_address
    return new_info

def updateStatus():
    ''' Update status information in amazon_list '''

    global amazon_list
    id_list = [instance['amazon_id'] for instance in amazon_list]
    status_info = ec2_client.describe_instance_status(InstanceIds = id_list, IncludeAllInstances=True)
    for status in status_info['InstanceStatuses']:
        for info in amazon_list:
            if info['amazon_id'] == status['InstanceId']:
                info['state'] = status['InstanceState']['Name']
                break

def setNumInstances(new_total_instances, instance_type, image_id):
    ''' 
    Change the number of running instances

    @param new_total_instances: New number of instances
    @param instance_type: Instance type for new instances
    @param image_id: ID of image (ami-xxxxxxxx)
    '''

    global amazon_list
    orig_total_instances = len(amazon_list)
    
    delta_instances = new_total_instances - orig_total_instances

    if delta_instances > 0:

        closeDispyScheduler()
        resetInstances()

        new_instances = ec2_res.create_instances(ImageId=image_id, MinCount=delta_instances, 
                                                      MaxCount=delta_instances, InstanceType=instance_type, 
                                                      SecurityGroups=[aws_security_group], KeyName=aws_key_name)

        for instance in new_instances:
            instance.create_tags(Tags=[{'Key':'Name','Value':'CAD_Cloud_' + instance.id}])
            new_info = generateInfo(instance)
            amazon_list.append(new_info)


    elif delta_instances < 0:
        ec2_client.terminate_instances(InstanceIds=[a['amazon_id'] for a in 
                                                         amazon_list[delta_instances:]])

        amazon_list = amazon_list[:new_total_instances]

        if new_total_instances != 0:
            resetInstances()
        

    if new_total_instances not in (orig_total_instances, 0):
        createTunnels()
        startDispyNode()
        startDispyScheduler()

        
def createTunnels():
    ''' Create reverse ssh tunnels to all instances '''

    def good_connection(instance_ip):
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            test_socket.connect((instance_ip, 22))
            return True
        except socket.error:
            return False     

    while len([i for i in amazon_list if i['tunnel'] == None]) > 0:
        time.sleep(5)            
        for instance in amazon_list:
            if instance['tunnel'] == None and instance['state'] == 'running' \
               and good_connection(instance['ip_address']):

                try:
                    instance['tunnel'] = \
                                ReverseTunnel(instance['ip_address'], 'ubuntu',
                                              pem_file,51347, '127.0.0.1',51347, check=30)
                    instance['tunnel'].create_reverse_tunnel()
                except SSHException:
                    print('cannot create tunnel')
                    instance['tunnel'] = 'NA'

        updateStatus()

    time.sleep(10)

def startDispyNode():
    ''' Start dispy on each Amazon instance '''
    
    dispy_pass = config.getDispyPassword()

    if dispy_pass == None:
        dispy_pass = ''.join([random.choice(string.ascii_letters + string.digits)
                              for x in range(20)])
        config.writeConfigValue('Dispy','password', dispy_pass)

    command = 'bash -c "export PATH=/home/ubuntu/miniconda3/bin:$PATH; source activate py36; /home/ubuntu/dispy/ssh_dispy.sh'


    for instance in amazon_list:
        stdin, stdout, stderr = instance['tunnel'].ssh.exec_command(command + " '" + dispy_pass + "'\"")

    # Need to give ample time for dispynode to start
    time.sleep(60)


def resetInstances():
    '''
    Reboot Amazon instances
    '''
    global amazon_list

    instanceids = [instance['amazon_id'] for instance in amazon_list]

    if len(amazon_list) > 0:
        ec2_client.reboot_instances(InstanceIds = instanceids)

        for instance in amazon_list:
            if instance['tunnel'] != None:
                if instance['tunnel'] != 'NA':
                    instance['tunnel'].event.set()
                    del instance['tunnel']
                    
                instance['tunnel'] = None
    
def reset():
    ''' Close and clear Amazon List '''
    closeDispyScheduler()
    
    clearAmazonList()
        
def close():
    ''' Shutdown all instances, close dispy scheduler and clear Amazon list '''

    setNumInstances(0)        
    closeDispyScheduler()

    clearAmazonList()    


def clearAmazonList():
    ''' Shutdown connection tunnels to Amazon instances and clear amazon list '''
    global amazon_list


    for instance in amazon_list:
        if instance['tunnel'] != None:
            instance['tunnel'].event.set()
            del instance['tunnel']
            instance['tunnel'] = None
    

    amazon_list = []
