# Lead 批准：R201-B T1 合成模拟器实现 + 资格门（不批结果/T2/T3/真实响应/湿实验）

2026-10-28。依据：R201-B 经 v0.1→v0.4 四轮修订与三轮独立挑战；B.3-C1 判 **approve_mvp_to_lead**（仅 T1 实现+资格门），SHA/算术一致。

## 批准范围（仅 T1 实现 + 资格门）
- 批准对象（v0.4 冻结链）：PROBLEM `D6B37E704DE141FE481A73D4BDDC0FFA6CBB0BA7FA6A686004D568415E6C5C99`；DESIGN `9112EDDC3180BA6101DF76CB34282BE84E7E9DF0EBD3EC714C4999388E7D01CD`；design_B_revision `E4968C701DB031BF246767D821A31DC5B8EF9AB50D3A0694462E023F661A3A5E`；json `A2D0CC1A01A9EF29FC7B2F0ACDC21658AFCEF6EE9D1F1FDC0829E3CC16601AA1`；report `31F17B5EF3CE98685ADA837B369837E081C43BC828C7D50071E1B6C7C9D472B0`；record `7A3F3A23E5663E49A738054F48B7A80CDD6F11B2684091E6D833581711C532FD`；usage `2AE7097824BABC8AE8013B74C4D318E02E76B807E4A6ABA1EFE57312948FBE0E`。
- 冻结：primary=(1200s,16 integer keys,κ=1,σ=0.10)、500 独立 replicate=500 decision units、MDE 0.088594≤0.10；敏感性 17×50 仅描述/cost_sensitive；**10 arms**（π_dual+C0–C6+C7 两臂）；primary 5,000/sensitivity 8,500/total 13,500/pilot 100 arm-runs；wall 单次≤45min/两跑≤90min + fallback；整数 key+正确 filler（1 CU/blank/QC well，价格假设须在实现/记录标注；若改用 A5 per-well 价需重算并披露）；x1/x2/EV 网格/证书阶梯/R_max=5；H_B AND、主检验仅 primary、best-single inner validation、测试集不 max。
- **资格门先于结果**：oracle 可恢复/null FP/EV 近似门/成本账/无泄漏/10 arms/两跑逐字节/schema/wall/hash。失败只写 `design_invalid`，不报 selection accuracy/top-k/regret。

## 非阻塞实现备注（写入实现/记录）
1) filler well 现按 1 CU/blank/QC well 计价（`filler wells=ceil(residual_CU)`）；若按物理 A5 assay well（≈5.3–10.7 CU/well）会超 T，须改用 A5 价重算或保持合成价并标注。
2) EV 门是"有限离散参考一致性门"，**不得写 EV exact**；建议更高分辨率参考或明确仅 T1 资格检查。
3) σ=0.10 噪声五点网格；敏感性 σ=0.05 须预注册对应五点网格（或 fallback 跳过敏感性）；EV 校准 replicate 数/seed 写入实现记录。

## 不批准
- 不批 T1 结果解释/决策收益；不批 T2/T3 执行；不批 O'Neil/Validation 真实响应读取/湿实验。
- 不称新颖性/机制/迁移/决策收益/独立确认；冻结≠资源足够/关系成立/Stage1/效果。
