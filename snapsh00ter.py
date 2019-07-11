#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
import boto3
from time import sleep

# configuration
REGION="us-west-2"
AVAILZONE="us-west-2b"
INSTANCEID="i-xxxxxxxx"
SSHCMD="ssh -i '~/.aws/key.pem' ec2-user@ec2-IP.us-west-2.compute.amazonaws.com"

def print_header():
    print("""
                              __             __         
      ___ ___  ___ ____  ___ / /  ___  ___  / /____ ____
     (_-</ _ \/ _ `/ _ \(_-</ _ \/ _ \/ _ \/ __/ -_) __/
    /___/_//_/\_,_/ .__/___/_//_/\___/\___/\__/\__/_/   
                 /_/
    A tool to search public AWS snapshots.
    Prerequisites: configured aws account, boto3 and aws cli installed
    Predefined snapshot filters: encrypted=false, state=completed
    """)

def get_snapshots():
    client = boto3.client('ec2', region_name=REGION)
    response = client.describe_regions()
    regionnames = [region['RegionName'] for region in response['Regions']]
    snapshots = []

    print("[*] Requesting Snapshots")
    for regionname in regionnames:
        snapshots_in_region = client.describe_snapshots(
            Filters=[
                {
                    'Name': 'status',
                    'Values': [
                        'completed',
                    ]
                },
                {
                    'Name': 'encrypted',
                    'Values': [
                        'false',
                    ]
                },
            ]
            )
        snapshots += snapshots_in_region['Snapshots']
    return snapshots

def filter_snapshots(snapshots, keywords=["backup"]):
    """
    accepts a list of snapshots and a list of keywords.
    returns a filtered list where an entry contains at least one of
    the keywords
    """
    print("[*] Filtering Snapshots")
    result_snaps = []
    for key in keywords:
        result_snaps += [snap for snap in snapshots if key in snap['Description']]
        #TODO case insensitive matching
    # TODO sort
    return result_snaps

def list_snapshots(snapshots):
    """
    pretty prints the snapshots
    """
    for index, snap in enumerate(snapshots):
        print('[{}]:'.format(index))
        print('  Description: {}'.format(snap['Description']))
        print('  VolumeSize:  {}'.format(snap['VolumeSize']))
        print('  SnapshotId:  {}'.format(snap['SnapshotId']))
        print('  StartTime:   {}'.format(str(snap['StartTime'])))
        print('\n')

def choose_snapshot(snapshots):
    """
    Let the user choose a snapshot among a list of snapshots.
    """
    choice = int(input('Choose a snapshot (the corresponding number): '))
    return snapshots[choice]

def create_attach_snapshot(snapshot):
    """
    attach volume to instance in /dev/sdf
    """
    print("[*] Creating the volume")
    client = boto3.client('ec2', region_name=REGION)
    response = client.create_volume(
        AvailabilityZone = AVAILZONE,
        SnapshotId = snapshot['SnapshotId'],
    )
    volumeid = response['VolumeId']
    print("[*] Volume created. VolumeId is {}.".format(volumeid))

    sleep(10)

    print("[*] Attaching the volume")
    response = client.attach_volume(
        InstanceId = INSTANCEID,
        VolumeId = volumeid,
        Device = '/dev/sdf'
    )

def interactive_shell(chosen_snapshot):
    """
    Open up an interactive SSH session to the defined instance with an attached volume from snapshot
    """
    print(os.system(SSHCMD + " 'sudo mount /dev/sdf1 /mnt'"))
    os.system(SSHCMD)

if __name__ == "__main__":
    print_header()
    snapshots = get_snapshots()
    filtered_snapshots = filter_snapshots(snapshots)
    list_snapshots(filtered_snapshots)
    chosen_snapshot = choose_snapshot(filtered_snapshots)
    create_attach_snapshot(chosen_snapshot)
    interactive_shell(chosen_snapshot)
