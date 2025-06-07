from hdfs import InsecureClient
import subprocess
import requests


# hdfs config
hdfs_url = 'http://192.168.2.10:9870'
hdfs_user = 'phamcongthuan'

client = InsecureClient(hdfs_url, user=hdfs_user)

def upload_to_hdfs(local_path, hdfs_path):
    client.upload(hdfs_path, local_path, overwrite=True)

def list_hdfs_files(hdfs_dir):
    return client.list(hdfs_dir)

def delete_hdfs_file(hdfs_path):
    client.delete(hdfs_path)

def download_from_hdfs(hdfs_path, local_path):
    client.download(hdfs_path, local_path, overwrite=True)

def rename_hdfs_file(old_hdfs_path, new_hdfs_path):
    client.rename(old_hdfs_path, new_hdfs_path)
