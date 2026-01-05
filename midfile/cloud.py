"""云存储操作模块"""
import datetime
import os
import logging
from boto3.session import Session
from botocore.exceptions import ClientError, BotoCoreError
from .config import get_cloud_config

logger = logging.getLogger(__name__)


def client():
    """创建云存储客户端"""
    try:
        config = get_cloud_config()
        access_key = config.get('access_key')
        secret_key = config.get('secret_key')
        endpoint = config.get('endpoint')
        
        if not all([access_key, secret_key, endpoint]):
            raise ValueError('配置文件中缺少必要的 cloud 配置项')
        
        session = Session(access_key, secret_key)
        s3_client = session.client('s3', endpoint_url=endpoint)
        return s3_client
    except Exception as e:
        logger.error(f'创建 cloud 客户端失败: {e}')
        raise


def get_default_bucket():
    """从配置文件获取默认bucket"""
    try:
        config = get_cloud_config()
        return config.get('bucket')
    except Exception as e:
        logger.warning(f'获取默认bucket失败: {e}')
        return None


def upload_file2cloud(s3, bucket, localpath, cloudpath):
    """上传文件到cloud"""
    try:
        s3.upload_file(localpath, bucket, cloudpath)
        logger.info(f'{localpath} upload to {bucket}/{cloudpath} finished!')
    except (ClientError, BotoCoreError) as e:
        logger.error(f'上传文件失败: {e}')
        raise


def download_file(s3, bucket, key, filename):
    """从cloud下载文件"""
    start_time = datetime.datetime.now()
    logger.info(f'download start: {start_time}') 

    try:
        # 确保输出目录存在
        outdir = os.path.dirname(filename)
        if outdir and not os.path.exists(outdir):
            os.makedirs(outdir, exist_ok=True)
        
        s3.download_file(
            Bucket=bucket,
            Key=key,
            Filename=filename)
        end_time = datetime.datetime.now()
        logger.info(f'download finished: {end_time}')
    except (ClientError, BotoCoreError) as e:
        logger.error(f'下载文件失败: {e}')
        raise
    except OSError as e:
        logger.error(f'创建输出目录失败: {e}')
        raise 


def query_obj(s3, bucket_id, filename):
    """查询cloud对象是否存在"""
    try:
        result = s3.get_object(Bucket=bucket_id, Key=filename)
        return result
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'NoSuchKey':
            logger.debug(f'{filename} not in bucket: {bucket_id}')
            return None
        else:
            logger.error(f'查询对象失败: {e}')
            raise
    except BotoCoreError as e:
        logger.error(f'查询对象失败: {e}')
        raise

