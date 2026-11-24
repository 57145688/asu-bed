# DWSIM 仿真结果摘要

- 模拟器：dwsim 9.0.5.0
- 物性方法：Peng-Robinson (PR)
- 收敛：True（converged，21 次迭代）
- 运行时间：2026-10-25T07:25:35Z；记录工具：cheme-as-code 0.8.0
- 设备/单元：21 个（simulated 20，excluded 1）

## 单元状态

| 单元 | 类型 | 状态 | 收敛 | 依据 |
|---|---|---|---|---|
| K1101 | compressor | simulated | True | predictive |
| C1101 | cooler | simulated | True | predictive |
| C1101U | cooler | simulated | True | predictive |
| V2101 | component_separator | simulated | True | specified |
| F2101 | heater | simulated | True | predictive |
| M2101 | mixer | simulated | True | predictive |
| E2101 | heater | simulated | True | predictive |
| X3102 | splitter | simulated | True | specified |
| K3101 | compressor | simulated | True | predictive |
| E3104 | cooler | simulated | True | predictive |
| E3105 | cooler | simulated | True | predictive |
| E3101 | multi_stream_exchanger | simulated | True | predictive |
| KT3101 | expander | simulated | True | predictive |
| C3101 | distillation_column | simulated | True | predictive |
| E3102 | multi_stream_exchanger | simulated | True | predictive |
| HL3101 | heater | simulated | True | predictive |
| C3102 | distillation_column | simulated | True | predictive |
| X3101 | splitter | simulated | True | specified |
| K4101 | compressor | simulated | True | predictive |
| K4102 | compressor | simulated | True | predictive |
| C1102 | None | excluded | None |  |

## 说明

- 本摘要来自 `process/simulation-run.json` 中 DWSIM 9.0.5 的实际收敛记录。
- 本机未安装 DWSIM 9.0.5（安装包 272 MB，当前网络约 11 KB/s，未完成下载），因此没有重新运行；重新运行的命令见 `bed/dwsim/README.md`。
- 结果只覆盖 `process/simulation.yaml` 声明的范围：排除了 H101、U801、K701；aMDEA 为指定分割；PR 缺少有来源的 kij。