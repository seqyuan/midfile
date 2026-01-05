"""命令行接口模块"""
import click
import os
import sys
import logging
import pandas as pd
from pathlib import Path
from .config import get_dbpath, update_config_dbpath, get_config_path
from .db import db_sql
from .cloud import client, get_default_bucket, upload_file2cloud, download_file, query_obj

# 初始化日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@click.group()
def main():
    """MidFile - 中间文件数据库管理系统"""
    pass


@main.command(name="init", short_help="初始化数据库")
@click.option('--dbdir', required=True, help='数据库目录路径')
def init(dbdir):
    """初始化数据库
    
    在指定的目录中初始化数据库，并更新配置文件中的 dbpath 值。
    同时将数据库目录和配置文件的权限设置为 777。
    """
    # 确保目录存在
    dbdir_path = Path(dbdir)
    dbdir_path.mkdir(parents=True, exist_ok=True)
    
    # 构建数据库文件路径（在 dbdir 目录中）
    dbpath = str(dbdir_path / 'midfile.db')
    
    # 更新配置文件中的 dbpath
    update_config_dbpath(dbpath)
    logger.info(f'已更新配置文件 dbpath: {dbpath}')
    
    # 初始化数据库
    with db_sql(dbpath) as tbj:
        tbj.crt_tb_sql()
    
    # 设置权限为 777
    try:
        os.chmod(dbdir_path, 0o777)
        logger.info(f'已设置目录权限: {dbdir_path}')
    except Exception as e:
        logger.warning(f'设置目录权限失败: {e}')
    
    try:
        os.chmod(dbpath, 0o777)
        logger.info(f'已设置数据库文件权限: {dbpath}')
    except Exception as e:
        logger.warning(f'设置数据库文件权限失败: {e}')
    
    # 也设置配置文件权限
    try:
        from .config import get_config_path
        config_path = get_config_path()
        os.chmod(config_path, 0o777)
        logger.info(f'已设置配置文件权限: {config_path}')
    except Exception as e:
        logger.warning(f'设置配置文件权限失败: {e}')
    
    print(f'成功创建数据库: {dbpath}')


@main.command(name="insert", short_help="insert one filepath to middlefile.db")
@click.option('--subprojectid', '-p', required=True,
              help='pmid or subprojectid (必需)')
@click.option('--product', '-r',
              help='产品或分析流程类型')
@click.option('--sample', '-s',
              help='sample name')
@click.option('--ftype', '-t',
              help='filetype')
@click.option('--fileformat', '-f',
              help='fileformat')
@click.option('--filepath', '-d',
              help='file local path')
def insert(subprojectid, product, sample, ftype, fileformat, filepath):
    """插入文件记录"""
    dbpath = get_dbpath()
    with db_sql(dbpath) as tbj:
        tbj.insert_tb_sql(subprojectid, product, sample, ftype, fileformat, filepath)
    print('插入记录成功')


@main.command(name="insert_ref", short_help="insert one subprojectID align and anno ref version to midfile.db")
@click.option('--subprojectid', '-p',
              help='pmid or subprojectid')
@click.option('--alignref', '-l',
              help='alignemnt ref version')
@click.option('--annoref', '-n',
              help='annotation ref version')
def ref_insert(subprojectid, alignref, annoref):
    """插入参考基因组版本记录"""
    dbpath = get_dbpath()
    with db_sql(dbpath) as tbj:
        query_sql = "SELECT * FROM ref WHERE pmid = ?"
        ref_df = pd.read_sql(query_sql, con=tbj.conn, params=(subprojectid,))
        
        if ref_df.shape[0] == 0:
            tbj.insert_tb_sql_ref(subprojectid, alignref, annoref)
            print('插入参考基因组记录成功')
        else:
            print(f'子项目 {subprojectid} 的参考基因组记录已存在')


@main.command(name="update", short_help="update middlefile.db")
@click.option('--filepath', '-d',
              help='file local path')
@click.option('--key', '-k',
              help='key name')
@click.option('--value', '-v',
              help='value text')
def update(filepath, key, value):
    """更新文件记录"""
    dbpath = get_dbpath()
    with db_sql(dbpath) as tbj:
        tbj.update_tb_value_sql(filepath, key, value)
    print('更新记录成功')


@main.command(name="l2c", short_help="upload file to cloud")
@click.option('--bucket', '-b',
              default=None,
              help='bucket名称，如果不指定则使用配置文件中的默认bucket')
@click.option('--local_path', '-l',
              help='file_local_path')
@click.option('--cloud_path', '-c',
              help='file cloud path')
def local2cloud(bucket, local_path, cloud_path):
    """上传本地文件到云存储"""
    if not os.path.exists(local_path):
        logger.error(f'本地文件不存在: {local_path}')
        sys.exit(1)
    
    # 如果未指定bucket，从配置文件读取默认值
    if bucket is None:
        bucket = get_default_bucket()
        if bucket is None:
            logger.error('未指定bucket且配置文件中没有默认bucket')
            sys.exit(1)
        logger.info(f'使用默认bucket: {bucket}')
    
    s3 = client()
    result = query_obj(s3, bucket, cloud_path)
    if result is not None:
        print('云上路径已存在')
    else:
        upload_file2cloud(s3, bucket, local_path, cloud_path)


@main.command(name="c2l", short_help="cloud file to local")
@click.option('--bucket', '-b',
              default=None,
              help='bucket名称，如果不指定则使用配置文件中的默认bucket')
@click.option('--cloud_path', '-c',
              help='file_cloud_path')
@click.option('--outpath', '-o',
              help='file download save path')
def cloud2local(bucket, cloud_path, outpath):
    """从云存储下载文件到本地"""
    # 如果未指定bucket，从配置文件读取默认值
    if bucket is None:
        bucket = get_default_bucket()
        if bucket is None:
            logger.error('未指定bucket且配置文件中没有默认bucket')
            sys.exit(1)
        logger.info(f'使用默认bucket: {bucket}')
    
    s3 = client()
    result = query_obj(s3, bucket, cloud_path)

    if result is not None:
        download_file(s3, bucket, cloud_path, outpath)
    else:
        logger.error(f'云上文件不存在: {cloud_path}')
        sys.exit(1)


@main.command(name="check", short_help="check if a filepath in the middlefile.db")
@click.option('--filepath', '-f', help='local file path')
def checkfile(filepath):
    """检查文件是否在数据库中"""
    dbpath = get_dbpath()
    with db_sql(dbpath) as tbj:
        df = tbj.check_file_sql(filepath)
    print(df)


@main.command(name="query_file", short_help="query filepath in the midfile.db")
@click.argument('outfile', metavar='<output_path>')
@click.option('--subprojectid', '-p', required=False,
              help='pmid or subprojectid')
@click.option('--product', '-r', required=False,
              help='产品或分析流程类型')
@click.option('--sample', '-s', required=False,
              help='sample name')
@click.option('--ftype', '-t', required=False,
              help='filetype')
@click.option('--fileformat', '-f', required=False,
              help='fileformat')
@click.option('--filepath', '-d', required=False,
              help='file local path')
def queryfile(outfile, subprojectid, product, sample, ftype, fileformat, filepath):
    """查询文件记录并导出"""
    notnone_para = {}
    if subprojectid is not None:
        notnone_para['pmid'] = subprojectid
    if product is not None:
        notnone_para['product'] = product
    if sample is not None:
        notnone_para['sample'] = sample
    if ftype is not None:
        notnone_para['ftype'] = ftype
    if fileformat is not None:
        notnone_para['fileformat'] = fileformat
    if filepath is not None:
        notnone_para['filepath'] = filepath

    if len(notnone_para) == 0:
        print('所有参数不能为空，请至少提供一个查询条件')
        sys.exit(1)

    dbpath = get_dbpath()
    with db_sql(dbpath) as tbj:
        df = tbj.query_recored(notnone_para)
    
    if df.shape[0] == 0:
        print('子项目编号+sample的组合未在后台数据库中查询到数据!')
        sys.exit(1)
    
    # 确保输出目录存在
    outdir = os.path.dirname(outfile)
    if outdir and not os.path.exists(outdir):
        os.makedirs(outdir, exist_ok=True)
    
    df.to_csv(outfile, sep='\t', index=False)
    print(f'查询结果已保存到: {outfile}')


@main.command(name="query_ref", short_help="query align and anno ref version")
@click.argument('outfile', metavar='<output_path>')
@click.option('--subprojectid', '-p', required=False,
              help='pmid or subprojectid')
def ref_query(outfile, subprojectid):
    """查询参考基因组版本记录并导出"""
    if subprojectid is None:
        print('子项目ID不能为空')
        sys.exit(1)
    
    dbpath = get_dbpath()
    with db_sql(dbpath) as tbj:
        query_sql = "SELECT * FROM ref WHERE pmid = ?"
        ref_df = pd.read_sql(query_sql, con=tbj.conn, params=(subprojectid,))

    if ref_df.shape[0] == 0:
        print('在后台数据库中未查询到 align和anno ref!')
        sys.exit(1)
    
    # 确保输出目录存在
    outdir = os.path.dirname(outfile)
    if outdir and not os.path.exists(outdir):
        os.makedirs(outdir, exist_ok=True)
    
    ref_df.to_csv(outfile, sep='\t', index=False)
    print(f'查询结果已保存到: {outfile}')


@main.command(name="info", short_help="显示 product, ftype, fileformat 的唯一值")
def info():
    """显示数据库中 product, ftype, fileformat 字段的唯一组合"""
    # 先输出配置文件位置
    config_path = get_config_path()
    print(f"配置文件位置: {config_path}")
    print()
    
    dbpath = get_dbpath()
    with db_sql(dbpath) as tbj:
        df = tbj.get_unique_values()
    
    # 打印表头
    print("product\tftype\tfileformat")
    
    # 打印每一行数据
    if not df.empty:
        for _, row in df.iterrows():
            product = row['product'] if pd.notna(row['product']) else ''
            ftype = row['ftype'] if pd.notna(row['ftype']) else ''
            fileformat = row['fileformat'] if pd.notna(row['fileformat']) else ''
            print(f"{product}\t{ftype}\t{fileformat}")


if __name__ == '__main__':
    main()

