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
pip install midfile
```

#### 使用 Poetry 安装（开发模式）

```bash
# 克隆仓库
git clone https://github.com/seqyuan/midfile.git
cd midfile

# 使用 Poetry 安装
poetry install

# 或使用 pip 安装（在项目目录下）
pip install -e .
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
- Windows：`%USERPROFILE%\.config\midfile.yml`
- 如果设置了 `XDG_CONFIG_HOME` 环境变量：`$XDG_CONFIG_HOME/midfile.yml`

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

**注意**：请勿将包含敏感信息的配置文件提交到版本控制系统。配置文件位置在用户目录下，每个用户有独立的配置。

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
数据库中的唯一值：

Product:
  - RNA-seq
  - scRNA-seq
  - ATAC-seq

Ftype:
  - raw
  - clean
  - filtered

Fileformat:
  - fastq
  - rds
  - gef
```

**说明**：该命令用于查看数据库中已使用的数据类型，方便用户了解数据库内容。

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

## 安全特性

1. **SQL注入防护**：所有数据库查询使用参数化查询，防止SQL注入攻击
2. **列名白名单**：更新和查询操作使用列名白名单验证，防止非法列名访问
3. **配置文件分离**：敏感信息（访问密钥）存储在用户配置文件中，不硬编码在代码中
4. **异常处理**：完善的异常处理和错误日志记录
5. **权限控制**：数据库目录和配置文件权限可根据需要设置

## 日志功能

程序使用 Python `logging` 模块记录操作日志，包括：
- 文件上传/下载操作
- 数据库操作
- 配置文件操作
- 错误信息

日志级别：INFO

## 注意事项

1. **文件路径唯一性**：`files` 表中的 `filepath` 字段是唯一的，不能重复插入相同路径的文件
2. **pmid 必填**：`pmid` 字段不能为空，插入记录时必须提供子项目ID
3. **配置文件安全**：请妥善保管 `~/.config/midfile.yml` 文件，不要泄露访问密钥
4. **数据库位置**：数据库文件路径可通过 `init` 命令指定，并会自动更新到配置文件中
5. **输出目录**：查询和下载操作会自动创建不存在的输出目录
6. **参考基因组记录**：`insert_ref` 命令会检查记录是否已存在，避免重复插入
7. **Bucket配置**：建议在配置文件中设置默认bucket，这样在使用 `l2c` 和 `c2l` 命令时无需每次都指定bucket
8. **数据库升级**：如果使用旧版本数据库，运行 `init` 或任何数据库操作时会自动升级表结构，添加 `product` 列
9. **配置文件自动初始化**：首次运行任何 `midfile` 命令时，会自动从包中拷贝配置文件模板到用户配置目录
10. **权限设置**：`init` 命令会将数据库目录和配置文件权限设置为 777，请根据实际安全需求调整

## 技术栈

- **Python 3.8+**
- **SQLite3**：轻量级数据库
- **Click**：命令行接口框架
- **Pandas**：数据处理和查询结果导出
- **PyYAML**：配置文件解析
- **Boto3**：AWS SDK（用于兼容 S3 协议的对象存储服务接口）
- **Poetry**：依赖管理和打包工具

## 项目结构

```
midfile/
├── pyproject.toml          # Poetry 配置文件
├── README.md               # 项目文档
├── midfile/                # Python 包
│   ├── __init__.py
│   ├── cli.py              # 命令行接口
│   ├── db.py               # 数据库操作
│   ├── cloud.py            # 云存储操作
│   ├── config.py           # 配置管理
│   └── midfile.yml         # 配置文件模板
└── .github/                # GitHub Actions 工作流
```

## 开发说明

### 代码结构

- `midfile/cli.py`：命令行接口，使用 Click 框架定义各种命令
- `midfile/db.py`：数据库操作类 `db_sql`，支持上下文管理器
- `midfile/cloud.py`：云存储操作，包括客户端创建、文件上传/下载等
- `midfile/config.py`：配置管理，包括配置文件加载、更新等
- `midfile/midfile.yml`：配置文件模板，会在首次运行时拷贝到用户配置目录

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/seqyuan/midfile.git
cd midfile

# 安装 Poetry（如果未安装）
curl -sSL https://install.python-poetry.org | python3 -

# 安装依赖
poetry install

# 激活虚拟环境
poetry shell

# 运行测试
poetry run midfile --help
```

### 构建和发布

```bash
# 构建包
poetry build

# 发布到 PyPI（需要配置 PyPI 凭证）
poetry publish
```

## 许可证

[请根据实际情况填写]

## 作者

Yuanzan <yuanzan@example.com>

## 贡献

欢迎提交 Issue 和 Pull Request！
