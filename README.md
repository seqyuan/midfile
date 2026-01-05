# MidFile - 中间文件数据库管理系统

## 项目简介

MidFile 是一个用于管理生物信息学分析过程中产生的中间文件的数据库管理系统。该系统提供了文件元数据管理、云存储集成和查询功能，帮助研究人员高效地组织和追踪分析流程中的各种中间数据文件。

## 核心功能

### 1. 数据库管理
- **SQLite 数据库**：使用轻量级 SQLite 数据库存储文件元数据
- **双表结构**：
  - `files` 表：存储文件元数据信息
  - `ref` 表：存储参考基因组版本信息
- **数据库初始化**：支持在指定目录初始化数据库，自动更新配置文件

### 2. 云存储集成
- **对象存储支持**：集成兼容 S3 协议的对象存储服务（如火山引擎 TOS、华为云 OBS、AWS S3 等）
- **文件上传**：将本地文件上传到云存储
- **文件下载**：从云存储下载文件到本地
- **文件检查**：检查云存储中文件是否存在

### 3. 文件元数据管理
- **文件信息记录**：记录文件的子项目ID、样本名、文件类型、格式、路径等信息
- **参考基因组版本管理**：记录每个子项目使用的比对和注释参考基因组版本
- **数据查询**：支持多条件组合查询文件记录
- **数据更新**：更新文件记录的特定字段

## 数据库结构

### files 表
存储文件元数据信息，包含以下字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键，自增 |
| pmid | TEXT | 子项目ID（subproject id），NOT NULL，不能为空 |
| product | TEXT | 产品或分析流程类型 |
| sample | TEXT | 样本名称。对于过滤数据（如raw/clean），为过滤后的样本名；对于分析报告中的中间数据，为结题报告中的样本名称，或用"all"等关键字表示整合数据 |
| ftype | TEXT | 文件类型，可配合fileformat区分文件（如raw/clean），或配合sample区分（如merge/integrate） |
| fileformat | TEXT | 文件格式，如：rds, fastq, gef, count, barcode, genes等 |
| filepath | TEXT | 本地文件路径，最好精确到文件而非目录。对于fastq文件，R1和R2应分别记录为两行。UNIQUE NOT NULL |
| cloudpath | TEXT | 云存储路径，统一存储在middlefile bucket |
| downpath | TEXT | 下载路径 |

### ref 表
存储参考基因组版本信息，包含以下字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键，自增 |
| pmid | TEXT | 子项目ID |
| alignref | TEXT | 比对参考基因组版本（信息搜集表中填写） |
| annoref | TEXT | 注释参考基因组版本（信息搜集表中填写） |

## 安装与配置

### 安装方式

#### 使用 pip 安装

```bash
pip install midfile -i https://pypi.org/simple
# pip install --upgrade midfile==0.1.5 -i https://pypi.org/simple
```


### 依赖要求

- Python >= 3.8
- click >= 8.0.0
- pyyaml >= 6.0
- pandas >= 1.3.0
- boto3 >= 1.26.0

### 配置文件

首次运行 `midfile` 命令时，程序会自动从包中拷贝配置文件模板到用户配置目录。

**配置文件位置**：
- Linux/macOS：`~/.config/midfile.yml`

**配置文件格式**：

```yaml
# 数据库路径
dbpath: /data/midfile.db

# 云存储配置（兼容 S3 协议）
cloud:
  access_key: "your_access_key"
  secret_key: "your_secret_key"
  endpoint: "https://your-endpoint.com"
  bucket: "your-bucket-name"
```

**配置说明**：
- `dbpath`: 数据库文件路径（可通过 `init` 命令自动更新）
- `access_key`: 对象存储访问密钥ID
- `secret_key`: 对象存储访问密钥Secret
- `endpoint`: 对象存储服务端点地址（例如：火山引擎 TOS、华为云 OBS、AWS S3 等）
- `bucket`: 默认bucket名称（可选，如果不指定则需要在命令中显式提供）

**支持的云存储服务**：
- 火山引擎 TOS
- 华为云 OBS
- AWS S3
- 其他兼容 S3 协议的对象存储服务

## 使用方法

### 初始化数据库

首次使用前需要初始化数据库。`init` 命令会在指定目录创建数据库文件，并自动更新配置文件中的 `dbpath` 值。

```bash
midfile init --dbdir <数据库目录路径>
```

**示例**：
```bash
midfile init --dbdir /data/midfile
```

**说明**：
- `--dbdir`：指定数据库目录路径（必需参数）
- 数据库文件将创建为 `<dbdir>/midfile.db`
- 配置文件中 `dbpath` 会自动更新为 `<dbdir>/midfile.db`
- 数据库目录和配置文件权限会被设置为 777

### 文件记录管理

#### 插入文件记录

```bash
midfile insert \
  --subprojectid <子项目ID> \
  [--product <产品或分析流程类型>] \
  --sample <样本名> \
  --ftype <文件类型> \
  --fileformat <文件格式> \
  --filepath <本地文件路径>
```

**示例**：
```bash
midfile insert \
  -p P001 \
  -r "RNA-seq" \
  -s sample1 \
  -t raw \
  -f fastq \
  -d /path/to/sample1_R1.fastq.gz
```

**参数说明**：
- `--subprojectid, -p`：子项目ID（必需）
- `--product, -r`：产品或分析流程类型（可选）
- `--sample, -s`：样本名称
- `--ftype, -t`：文件类型
- `--fileformat, -f`：文件格式
- `--filepath, -d`：本地文件路径

**注意**：`--subprojectid` 是必需参数，不能为空。

#### 更新文件记录

更新文件记录的特定字段（如cloudpath、downpath等）：

```bash
midfile update \
  --filepath <文件路径> \
  --key <字段名> \
  --value <新值>
```

**示例**：
```bash
midfile update \
  -d /path/to/file.fastq.gz \
  -k cloudpath \
  -v cloud://bucket/path/to/file.fastq.gz
```

**可更新的字段**：pmid, product, sample, ftype, fileformat, cloudpath, downpath

#### 检查文件是否存在

检查指定文件路径是否在数据库中：

```bash
midfile check --filepath <文件路径>
```

**示例**：
```bash
midfile check -f /path/to/file.fastq.gz
```

#### 查询文件记录

根据条件查询文件记录并导出到文件：

```bash
midfile query_file <输出文件路径> \
  [--subprojectid <子项目ID>] \
  [--product <产品或分析流程类型>] \
  [--sample <样本名>] \
  [--ftype <文件类型>] \
  [--fileformat <文件格式>] \
  [--filepath <文件路径>]
```

**示例**：
```bash
# 查询特定子项目和样本的所有文件
midfile query_file output.tsv \
  -p P001 \
  -s sample1

# 查询特定产品和格式的所有文件
midfile query_file output.tsv \
  -p P001 \
  -r "RNA-seq" \
  -f gef
```

**注意**：至少需要提供一个查询条件。查询结果会以制表符分隔的格式保存到指定文件。

#### 显示数据库信息

显示数据库中 `product`、`ftype`、`fileformat` 字段的唯一值：

```bash
midfile info
```

**示例输出**：
```
product	ftype	fileformat
RNA-seq	raw	fastq
RNA-seq	clean	fastq
scRNA-seq	raw	rds
scRNA-seq	filtered	rds
ATAC-seq	raw	fastq
```

**说明**：该命令用于查看数据库中 `product`、`ftype`、`fileformat` 的唯一组合，输出为制表符分隔的表格格式，方便用户了解数据库中的数据类型组合。

### 参考基因组版本管理

#### 插入参考基因组版本

为子项目记录比对和注释参考基因组版本：

```bash
midfile insert_ref \
  --subprojectid <子项目ID> \
  --alignref <比对参考基因组版本> \
  --annoref <注释参考基因组版本>
```

**示例**：
```bash
midfile insert_ref \
  -p P001 \
  -l GRCh38 \
  -n Ensembl_104
```

**说明**：如果该子项目的参考基因组记录已存在，将不会重复插入。

#### 查询参考基因组版本

查询子项目的参考基因组版本信息：

```bash
midfile query_ref <输出文件路径> \
  --subprojectid <子项目ID>
```

**示例**：
```bash
midfile query_ref ref_output.tsv -p P001
```

### 云存储操作

#### 上传文件到云存储

将本地文件上传到对象存储：

```bash
midfile l2c \
  [--bucket <bucket名称>] \
  --local_path <本地文件路径> \
  --cloud_path <云存储路径>
```

**示例**：
```bash
# 使用配置文件中的默认bucket
midfile l2c \
  -l /local/path/to/file.fastq.gz \
  -c path/to/file.fastq.gz

# 显式指定bucket（会覆盖配置文件中的默认值）
midfile l2c \
  -b my-bucket \
  -l /local/path/to/file.fastq.gz \
  -c path/to/file.fastq.gz
```

**说明**：
- 如果不指定 `--bucket`，会使用配置文件 `~/.config/midfile.yml` 中的 `bucket` 配置
- 如果配置文件中也没有指定，命令会报错
- 如果云上路径已存在，会提示"云上路径已存在"，不会重复上传

#### 从云存储下载文件

从对象存储下载文件到本地：

```bash
midfile c2l \
  [--bucket <bucket名称>] \
  --cloud_path <云存储路径> \
  --outpath <本地保存路径>
```

**示例**：
```bash
# 使用配置文件中的默认bucket
midfile c2l \
  -c path/to/file.fastq.gz \
  -o /local/path/to/downloaded_file.fastq.gz

# 显式指定bucket（会覆盖配置文件中的默认值）
midfile c2l \
  -b my-bucket \
  -c path/to/file.fastq.gz \
  -o /local/path/to/downloaded_file.fastq.gz
```

**说明**：
- 如果不指定 `--bucket`，会使用配置文件中的默认bucket
- 如果云上文件不存在，命令会报错
- 输出目录如果不存在会自动创建

## 命令列表

| 命令 | 简写 | 功能 | 必需参数 |
|------|------|------|----------|
| `init` | - | 初始化数据库 | `--dbdir`（必需） |
| `insert` | - | 插入文件记录 | `--subprojectid`（必需） |
| `insert_ref` | - | 插入参考基因组版本 | `--subprojectid`, `--alignref`, `--annoref` |
| `update` | - | 更新文件记录 | `--filepath`, `--key`, `--value` |
| `check` | - | 检查文件是否存在 | `--filepath` |
| `query_file` | - | 查询文件记录 | `<输出文件路径>` + 至少一个查询条件 |
| `query_ref` | - | 查询参考基因组版本 | `<输出文件路径>`, `--subprojectid` |
| `info` | - | 显示 product, ftype, fileformat 的唯一值 | - |
| `l2c` | - | 上传文件到云存储 | `--local_path`, `--cloud_path`（`--bucket`可选） |
| `c2l` | - | 从云存储下载文件 | `--cloud_path`, `--outpath`（`--bucket`可选） |


## 注意事项

1. **文件路径唯一性**：`files` 表中的 `filepath` 字段是唯一的，不能重复插入相同路径的文件
2. **pmid 必填**：`pmid` 字段不能为空，插入记录时必须提供子项目ID
3. **配置文件安全**：请妥善保管 `~/.config/midfile.yml` 文件，不要泄露访问密钥
4. **数据库位置**：数据库文件路径可通过 `init` 命令指定，并会自动更新到配置文件中
5. **输出目录**：查询和下载操作会自动创建不存在的输出目录
6. **参考基因组记录**：`insert_ref` 命令会检查记录是否已存在，避免重复插入
7. **Bucket配置**：建议在配置文件中设置默认bucket，这样在使用 `l2c` 和 `c2l` 命令时无需每次都指定bucket
8. **配置文件自动初始化**：首次运行任何 `midfile` 命令时，会自动从包中拷贝配置文件模板到用户配置目录
9. **权限设置**：`init` 命令会将数据库目录和配置文件权限设置为 777，请根据实际安全需求调整


## 作者

Yuan Zan <yfinddream@gmail.com>

## 贡献

欢迎提交 Issue 和 Pull Request！

## release
```
version="v0.1.5" && \
git add -A && git commit -m $version && git tag $version && git push origin main && git push origin $version
```