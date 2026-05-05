======================================================================
mml2tabular.py 测试报告
生成时间: 2026-05-05 10:42
测试目录: ~/workspace/mml-manager/converter/
======================================================================

【测试数据】test_sample.mml
  - 5 个表: SUBRACK(3), BOARD(5), LTE_CELL(5), NBRRELATION(5), CELLPARAM(8)
  - 共 26 条记录
  - 覆盖: 中文、特殊字符(逗号/引号)、数值字段、ADD/SET混合

======================================================================
测试 1: MML → Excel（默认模式）
----------------------------------------------------------------------
  命令: python mml2tabular.py test_sample.mml -o test_output
  结果: ✅ test_output.xlsx 生成成功
  验证: 5个Sheet, 26行数据, 表头蓝色样式, 中文/特殊字符正常
  表结构:
    - BOARD       : 6行 (ID排序 ✓)  列: DESC,ID,SLOT,SUBRACK_ID,TYPE,VERSION
    - CELLPARAM   : 9行 (ID排序 ✓)  列: CELL_NAME,CIO,ID,REMARKS,RSRP_BIAS,TX_POWER,TX_POWER_DYN_MAX,TX_POWER_DYN_MIN
    - LTE_CELL    : 6行 (ID排序 ✓)  列: BAND,COVER_RADIUS,FREQ,ID,NAME,PCI,TAC
    - NBRRELATION : 6行 (ID排序 ✓)  列: DST_CELL,HOTHRESH,ID,SRC_CELL
    - SUBRACK     : 4行 (ID排序 ✓)  列: ID,LOCATION,NAME,TYPE,VENDOR

======================================================================
测试 2: MML → CSV（--csv 模式）
----------------------------------------------------------------------
  命令: python mml2tabular.py test_sample.mml -o test_csv_output --csv
  结果: ✅ test_csv_output_csv/ 目录生成
  验证: 5个CSV文件, UTF-8 BOM编码, 表头和数据完整
  文件:
    - BOARD.csv       : 6行
    - CELLPARAM.csv   : 9行
    - LTE_CELL.csv    : 6行
    - NBRRELATION.csv : 6行
    - SUBRACK.csv     : 4行

======================================================================
测试 3: MML → Both（--both 模式）
----------------------------------------------------------------------
  命令: python mml2tabular.py test_sample.mml -o test_both_output --both
  结果: ✅ test_both_output.xlsx + test_both_output_csv/ 同时生成
  验证: Excel和CSV内容与单独模式一致

======================================================================
测试 4: 回环测试（Excel → MML）
----------------------------------------------------------------------
  命令: python tabular2mml.py test_output.xlsx -o roundtrip_test.mml
  结果: ✅ 26条记录全部回环转换成功
  验证: 数据完整无丢失，中文/特殊字符正确处理
  注意:
    - 原始MML中的 ADD CELLPARAM:ID=6 变为 SET（tabular2mml默认SET）
    - 含逗号的值转为 三重引号 格式（"""特殊值,含逗号"""）

======================================================================
测试 5: 错误处理
----------------------------------------------------------------------
  - 空MML文件: 提示"未找到有效的MML命令"
  - 缺失 openpyxl: 提示安装命令
  - 文件不存在: 友好提示

======================================================================
结论: ✅ 全部测试通过!
  mml2tabular.py 稳定运行，成功合并 mml2xls + mml2sql 功能。
======================================================================
