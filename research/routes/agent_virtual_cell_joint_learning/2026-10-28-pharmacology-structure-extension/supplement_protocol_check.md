# BCL11B 官方补充附件：协议资格核查

2026-10-28。P8定向附件核查，不改P7独立初稿、共享索引或机制记录。

**结果：官方独立入口HTTP403，未取得补充PDF。** 本次仅1次HTTP，timeout25s，15MB上限，未重试、换代理/身份或轮询。精确URL、UTC时刻、状态、Content-Type和错误响应字节hash见 `sources/bcl11b_official_supplement/receipt.json`。收到的是 `text/html; charset=UTF-8` 错误正文5654bytes，保留为 `http_error_body.bin`，不是PDF；未以PDF命名，未提取图注或功能数据。P7本代理累计7次HTTP（原6+本次1）。root此前EuropePMC supplementaryFiles超时属另一次已披露尝试，不计为本代理调用。

## 仍未核实的决定性字段

| 字段 | 资格 |
|---|---|
| TNFα×BCL11B表达救援×Doxo完整交叉设计，是否有明确S11/S12 legend | **unknown**。正文分别描述表达救援、TNFα状态抑制、TNFα+Doxo与KO背景，但未读取补充不能将这些分开实验拼成完整交叉。 |
| S3I/J再次Doxo的具体剂量 | **unknown**。原始正文sec5P4证实再生类器官仍响应Doxo，但此处未给足剂量，不能套用其他实验100/200nM。 |
| S3I/J撤药—单细胞再嵌入—重长—再次给药间隔与时长 | **unknown**。原始正文有顺序，准确间隔和时长未核。 |
| S3I/J独立培养、类器官/孔/实验重复层级 | **unknown**。不能以general methods ≥3次替代该panel的明确层级。 |
| S11/S12单细胞TNFα实验图注及方案 | **unknown**。正文相关描述可保留为P级证据，补充未读。 |

403仅证明本次入口拒绝访问，不证明作者未做实验、附件不存在或数据不可公开获得。既有正文证据不受此失败影响；本次不扩大检索。
